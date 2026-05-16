"""Anki integration and orchestration for the Pomodoro Qt UI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from aqt.qt import QAction, QDialog, QMessageBox, QTimer

from .analytics_store import PomodoroAnalyticsStore
from .anki_bridge import AnkiBridge
from .backup_manager import BackupManager
from .cards_studied import make_cards_studied_popover
from .changelog import CURRENT_VERSION, has_unseen
from .changelog_dialog import ChangelogDialog
from .config_store import ConfigStore
from .dialogs import BreakDoneDialog, CHOICE_END, EditTimeDialog, PomodoroDoneDialog
from .experience import make_experience_popover
from .experience_metric import ExperienceMetrics, level_state
from .i18n import set_language, tr
from .models import MODE_BREAK, MODE_POMODORO, PomodoroSettings, SessionMetrics, TimerRuntimeState
from .retention import make_retention_popover
from .revlog_metrics import RevlogMetricsSource
from .session_history import make_session_history_popover
from .session_manager import PomodoroSessionManager
from .study_time import make_study_time_popover
from .settings_dialog import SettingsDialog
from .storage import PomodoroDataStore, default_state
from .style import addon_qss
from .streaks import make_streak_popover
from .timer import PomodoroTimer
from .tracking import ReviewTracker
from .ui_components import addon_logo_icon
from .ui_manager import UIManager


ACCEPTED = QDialog.DialogCode.Accepted


class PomodoroAddonController:
    def __init__(self, mw, addon_package: str) -> None:
        self.mw = mw
        self.addon_package = addon_package
        self._profile_active = True
        self._profile_folder = self._current_profile_folder()
        self.config_store = ConfigStore(mw, addon_package)
        self.settings = self.config_store.load()
        set_language(self.settings.language)

        self.data_store = PomodoroDataStore(mw, addon_package)
        self.analytics_store = PomodoroAnalyticsStore(mw, addon_package)
        self.revlog_metrics_source = RevlogMetricsSource(mw)
        self.session_manager = PomodoroSessionManager(self.data_store, self.analytics_store)
        self.metrics = self.session_manager.metrics()
        self._apply_revlog_metrics()
        self.timer = PomodoroTimer(self.settings)
        self.timer.restore_state(self.session_manager.timer_state())
        self.tracker = ReviewTracker(self._on_review_answered, self._deck_name_for_id)

        self.ui = UIManager(
            mw,
            self._make_metric_popover,
            self._refresh_metric_popover,
            self._toggle_timer_pause,
            self._stop_timer,
            self._edit_timer_duration,
            self.open_settings,
            self._save_corner_position,
        )
        self.backup_manager = self._make_backup_manager()
        self.anki_bridge = AnkiBridge(
            self._on_anki_state_changed,
            self._on_reviewer_refreshed,
            self.tracker.on_pre_answer,
            self.tracker.on_did_answer,
            self.tracker.on_reviewer_end,
            self._on_profile_will_close,
        )

        self._last_completed_metrics: Optional[SessionMetrics] = None
        self._last_timer_signature = None
        self._revlog_refresh_timer = QTimer(mw)
        self._revlog_refresh_timer.setSingleShot(True)
        self._revlog_refresh_timer.timeout.connect(self._refresh_revlog_metrics_after_answer)
        self._anki_day_refresh_timer = QTimer(mw)
        self._anki_day_refresh_timer.setSingleShot(True)
        self._anki_day_refresh_timer.timeout.connect(self._on_anki_day_rollover)
        self.settings_action: Optional[QAction] = None
        self._storage_warning_shown = False
        self._config_warning_shown = False
        self._setup_done = False

    def setup(self) -> None:
        if self._setup_done:
            return
        self._setup_done = True
        self.ui.build(
            self.settings,
            self.metrics,
            self.experience_metrics,
            self.cards_metrics,
            self.retention_metrics,
            self.streak_metrics,
            self.study_time_metrics,
            self.session_manager.audio_state(),
        )
        self._connect_timer()
        self._sync_timer_state()
        self._mark_timer_started_if_running()
        self._add_menu_action()
        self.anki_bridge.install()
        self._schedule_anki_day_refresh()
        QTimer.singleShot(0, self.update_visibility)
        QTimer.singleShot(800, self._maybe_show_changelog)

    def rebind_profile(self, mw=None) -> None:
        """Rebuild profile-local state after Anki opens or switches profile."""
        if mw is not None:
            self.mw = mw
        self._profile_active = True
        self._profile_folder = self._current_profile_folder()
        self._log_profile_event("profile_did_open.rebind.begin")

        self._revlog_refresh_timer.stop()
        self._anki_day_refresh_timer.stop()
        self.ui.hide_floating_popovers()
        self.tracker.on_reviewer_end()

        self.config_store = ConfigStore(self.mw, self.addon_package)
        self.settings = self.config_store.load()
        set_language(self.settings.language)
        self.data_store = PomodoroDataStore(self.mw, self.addon_package)
        self.analytics_store = PomodoroAnalyticsStore(self.mw, self.addon_package)
        self.revlog_metrics_source = RevlogMetricsSource(self.mw)
        self.session_manager = PomodoroSessionManager(self.data_store, self.analytics_store)
        self.backup_manager = self._make_backup_manager()

        self.metrics = self.session_manager.metrics()
        self._apply_revlog_metrics()
        self._last_completed_metrics = None
        self._last_timer_signature = None
        self._storage_warning_shown = False

        self.timer.apply_settings(self.settings)
        self.timer.restore_state(self.session_manager.timer_state())
        self._update_menu_text()
        self._rebuild_ui()
        self.update_visibility()
        self._schedule_anki_day_refresh()
        self._log_profile_event("profile_did_open.rebind.done")

    def _make_backup_manager(self) -> BackupManager:
        return BackupManager(
            lambda: self.settings,
            lambda: self.data_store.load(),
            lambda: self.analytics_store.export_data(),
            self._save_runtime_state,
            self._apply_imported_backup,
        )

    def update_visibility(self) -> None:
        self.ui.update_visibility(self.settings)

    def _maybe_show_changelog(self) -> None:
        try:
            state = self.data_store.load()
        except Exception:
            return
        if not isinstance(state, dict):
            return
        if bool(state.get("suppress_changelog_popup", False)):
            return
        last_seen = str(state.get("last_changelog_version", "") or "")
        if last_seen == CURRENT_VERSION:
            return
        if not has_unseen(last_seen):
            self._record_changelog_seen(state, suppress=False)
            return
        try:
            dialog = ChangelogDialog(self.mw, last_seen)
            dialog.setStyleSheet(addon_qss(self.settings.theme))
            dialog.exec()
            self._record_changelog_seen(state, suppress=dialog.dont_show_again)
        except Exception:
            return

    def _record_changelog_seen(self, state: dict, suppress: bool) -> None:
        state = dict(state) if isinstance(state, dict) else default_state()
        state["last_changelog_version"] = CURRENT_VERSION
        state["suppress_changelog_popup"] = bool(suppress)
        try:
            self.data_store.save(state)
        except Exception:
            pass

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.mw, self.settings)
        dialog.setStyleSheet(addon_qss(self.settings.theme))
        dialog.export_requested.connect(lambda: self.backup_manager.export_backup(dialog))
        dialog.import_requested.connect(lambda: self._import_backup_from_dialog(dialog))
        dialog.reset_data_requested.connect(lambda: self._reset_study_data_from_dialog(dialog))
        dialog.reset_all_requested.connect(lambda: self._reset_all_from_dialog(dialog))
        dialog.apply_requested.connect(lambda: self._apply_settings_from_dialog(dialog))
        if _dialog_accepted(dialog):
            self._apply_settings_from_dialog(dialog)

    def _import_backup_from_dialog(self, dialog: SettingsDialog) -> None:
        if self.backup_manager.import_backup(dialog):
            dialog.reject()

    def _reset_study_data_from_dialog(self, dialog: SettingsDialog) -> None:
        if self._reset_data(dialog, reset_settings=False):
            dialog.reject()

    def _reset_all_from_dialog(self, dialog: SettingsDialog) -> None:
        if self._reset_data(dialog, reset_settings=True):
            dialog.reject()

    def _apply_settings_from_dialog(self, dialog: SettingsDialog) -> None:
        self._save_runtime_state()
        self.settings = dialog.to_settings(self.settings)
        set_language(self.settings.language)
        if not self.config_store.save(self.settings):
            self._warn_config_failure_if_needed()
        self.timer.apply_settings(self.settings)
        self._update_menu_text()
        self._rebuild_ui()
        self.update_visibility()

    def _connect_timer(self) -> None:
        self.timer.changed.connect(self._sync_timer_state)
        self.timer.pomodoro_completed.connect(self._on_pomodoro_completed)
        self.timer.break_completed.connect(self._on_break_completed)
        self.timer.pomodoro_done.connect(self._show_done_dialog)
        self.timer.break_done.connect(self._show_break_done_dialog)

    def _add_menu_action(self) -> None:
        menu = getattr(getattr(self.mw, "form", None), "menuTools", None)
        if menu is None:
            return
        action = QAction(tr("menu.settings"), self.mw)
        action.setIcon(addon_logo_icon())
        action.triggered.connect(self.open_settings)
        menu.addAction(action)
        self.settings_action = action

    def _update_menu_text(self) -> None:
        if self.settings_action is not None:
            self.settings_action.setText(tr("menu.settings"))

    def _on_anki_state_changed(self, *args) -> None:
        QTimer.singleShot(0, self.update_visibility)

    def _on_reviewer_refreshed(self, *args) -> None:
        QTimer.singleShot(0, self.update_visibility)

    def _on_profile_will_close(self, *args) -> None:
        self._log_profile_event("profile_will_close.begin")
        self._revlog_refresh_timer.stop()
        self._anki_day_refresh_timer.stop()
        self._save_runtime_state()
        self.tracker.on_reviewer_end()
        self.timer.suspend()
        self.ui.hide_floating_popovers()
        self.ui.hide_all_layouts()
        self._profile_active = False
        self._log_profile_event("profile_will_close.done")

    def _sync_timer_state(self, *args) -> None:
        if not self._profile_active:
            return
        state = self.timer.state()
        self.ui.sync_timer_state(state)
        signature = (state.mode, state.total_seconds, state.paused, state.started)
        if self._last_timer_signature is not None and signature != self._last_timer_signature:
            self._save_timer_state()
        self._last_timer_signature = signature

    def _toggle_timer_pause(self) -> None:
        self.timer.toggle_pause()
        if not self.timer.paused:
            self.metrics = self.session_manager.mark_timer_started()
            self._warn_storage_failure_if_needed()
            self._display_metrics()
        self._save_timer_state()

    def _stop_timer(self) -> None:
        duration_seconds = max(0, self.timer.total_seconds - self.timer.time_left)
        self.metrics = self.session_manager.stop_current_session(self.timer.mode, duration_seconds)
        self._warn_storage_failure_if_needed()
        self.timer.stop()
        self._save_timer_state()
        self._display_metrics()

    def _edit_timer_duration(self) -> None:
        dialog = EditTimeDialog(self.mw, self.settings)
        dialog.setStyleSheet(addon_qss(self.settings.theme))
        if not _dialog_accepted(dialog):
            return
        new_pomodoro = int(dialog.pomodoro_minutes)
        new_break = int(dialog.break_minutes)
        if new_pomodoro == self.settings.pomodoro_minutes and new_break == self.settings.break_minutes:
            return

        self._save_runtime_state()
        self.settings.pomodoro_minutes = new_pomodoro
        self.settings.break_minutes = new_break
        if not self.config_store.save(self.settings):
            self._warn_config_failure_if_needed()
        self.timer.apply_settings(self.settings)
        self._sync_timer_state()
        self._save_timer_state()

    def _on_pomodoro_completed(self) -> None:
        self._last_completed_metrics = self.session_manager.complete_pomodoro(self.timer.total_seconds)
        self._warn_storage_failure_if_needed()
        self.metrics = self.session_manager.metrics()
        self._display_metrics()

    def _on_break_completed(self) -> None:
        self.metrics = self.session_manager.complete_break(self.timer.total_seconds)
        self._warn_storage_failure_if_needed()
        self._display_metrics()
        QTimer.singleShot(0, self._mark_timer_started_if_running)

    def _show_done_dialog(self) -> None:
        dialog = PomodoroDoneDialog(self.mw, self.settings, self._last_completed_metrics or self.metrics)
        dialog.setStyleSheet(addon_qss(self.settings.theme))
        if _dialog_accepted(dialog):
            if dialog.choice == CHOICE_END:
                self.timer.stop()
                self._save_timer_state()
                self._refresh_metrics()
                return
            if dialog.choice == MODE_BREAK and dialog.break_minutes != self.settings.break_minutes:
                self.settings.break_minutes = int(dialog.break_minutes)
                self.config_store.save(self.settings)
                self.timer.apply_settings(self.settings)
            self.timer.start_mode(dialog.choice)
            if dialog.choice == MODE_POMODORO:
                self._mark_timer_started_if_running()
            self._save_timer_state()

    def _show_break_done_dialog(self) -> None:
        dialog = BreakDoneDialog(self.mw, self.settings)
        dialog.setStyleSheet(addon_qss(self.settings.theme))
        if _dialog_accepted(dialog):
            if dialog.choice == CHOICE_END:
                self.timer.stop()
                self._save_timer_state()
                self._refresh_metrics()
                return
            if dialog.pomodoro_minutes != self.settings.pomodoro_minutes:
                self.settings.pomodoro_minutes = int(dialog.pomodoro_minutes)
                self.config_store.save(self.settings)
                self.timer.apply_settings(self.settings)
            self.timer.start_mode(MODE_POMODORO)
            self._mark_timer_started_if_running()
            self._save_timer_state()

    def _save_corner_position(self, left: int, top: int) -> None:
        self.settings.corner_left = left
        self.settings.corner_top = top
        if not self.config_store.save(self.settings):
            self._warn_config_failure_if_needed()

    def _on_review_answered(self, event) -> None:
        if not self._ensure_current_profile_bound():
            return
        self.metrics = self.session_manager.record_answer(event)
        self.revlog_metrics_source.note_review_answered(getattr(event, "ease", None))
        self._warn_storage_failure_if_needed()
        self._display_metrics()
        self._schedule_revlog_refresh()

    def _mark_timer_started_if_running(self) -> None:
        if self.timer.mode != MODE_POMODORO or self.timer.paused:
            return
        self.metrics = self.session_manager.mark_timer_started()
        self._warn_storage_failure_if_needed()
        self._save_timer_state()
        self._display_metrics()

    def _refresh_metrics(self) -> None:
        self.metrics = self.session_manager.metrics()
        self._display_metrics()

    def _refresh_revlog_metrics_after_answer(self) -> None:
        self.revlog_metrics_source.invalidate_today_snapshot()
        self._refresh_metrics()

    def _display_metrics(self) -> None:
        self._apply_revlog_metrics()
        self.ui.refresh_metrics(
            self.metrics,
            self.experience_metrics,
            self.cards_metrics,
            self.retention_metrics,
            self.streak_metrics,
            self.study_time_metrics,
        )
        self._schedule_anki_day_refresh()

    def _make_metric_popover(self, name: str):
        if name == "session":
            return make_session_history_popover(self.metrics, self.session_manager.history_popover_snapshot())
        if name == "experience":
            return make_experience_popover(self.experience_metrics)
        if name == "cards":
            return make_cards_studied_popover(self.cards_metrics)
        if name == "retention":
            return make_retention_popover(self.retention_metrics)
        if name == "streak":
            return make_streak_popover(self.streak_metrics)
        if name == "study_time":
            return make_study_time_popover(self.study_time_metrics)
        return None

    def _refresh_metric_popover(self, name: str, popover) -> None:
        if name == "session":
            popover.refresh_data(self.metrics, self.session_manager.history_popover_snapshot())
            return
        if name == "streak":
            popover.refresh_data(self.streak_metrics)
            return
        if name == "experience":
            popover.refresh_data(self.experience_metrics)
            return
        if name == "retention":
            popover.refresh_data(self.retention_metrics)
            return
        if name == "cards":
            popover.refresh_data(self.cards_metrics)
            return
        if name == "study_time":
            popover.refresh_data(self.study_time_metrics)
            return
        if hasattr(popover, "refresh_data"):
            popover.refresh_data(self.metrics)

    def _apply_revlog_metrics(self) -> None:
        snapshot = self.revlog_metrics_source.metrics()
        self.cards_metrics = snapshot.cards
        total_experience = max(0, snapshot.experience.experience)
        level = level_state(total_experience)
        self.experience_metrics = ExperienceMetrics(
            level=level["level"],
            experience=total_experience,
            level_floor_experience=level["floor_experience"],
            next_level_experience=level["next_level_experience"],
            experience_to_next_level=level["experience_to_next_level"],
            level_progress=level["progress"],
            streak_days=snapshot.experience.streak_days,
            unique_cards=snapshot.experience.unique_cards,
            again_cards=snapshot.experience.again_cards,
            hard_cards=snapshot.experience.hard_cards,
            good_cards=snapshot.experience.good_cards,
            easy_cards=snapshot.experience.easy_cards,
        )
        self.retention_metrics = snapshot.retention
        self.streak_metrics = snapshot.streak
        self.study_time_metrics = snapshot.study_time

    def _schedule_anki_day_refresh(self) -> None:
        seconds = max(1, int(self.revlog_metrics_source.seconds_until_cutoff()))
        delay_ms = (seconds + 2) * 1000
        self._anki_day_refresh_timer.start(delay_ms)

    def _schedule_revlog_refresh(self) -> None:
        self._revlog_refresh_timer.start(250)

    def _on_anki_day_rollover(self) -> None:
        self._refresh_metrics()

    def _deck_name_for_id(self, deck_id: Optional[int]) -> str:
        if deck_id is None:
            return ""
        try:
            decks = self.mw.col.decks
            name = decks.name(deck_id)
            return str(name or "")
        except Exception:
            try:
                deck = self.mw.col.decks.get(deck_id)
                return str(deck.get("name") or "") if isinstance(deck, dict) else ""
            except Exception:
                return ""

    def _save_runtime_state(self) -> None:
        if not self._profile_active or not self._ensure_current_profile_bound():
            return
        self._log_profile_event("save_runtime_state")
        if not self.session_manager.save_audio_state(self.ui.audio_state_snapshot()):
            self._warn_storage_failure_if_needed()
        self._save_timer_state()

    def _save_timer_state(self) -> None:
        if not self._profile_active:
            return
        if not self.session_manager.save_timer_state(self.timer.runtime_state()):
            self._warn_storage_failure_if_needed()
        else:
            self._warn_storage_failure_if_needed()

    def _apply_imported_backup(self, settings, state: dict, analytics: dict) -> None:
        self.ui.hide_floating_popovers()
        self.settings = settings
        set_language(self.settings.language)
        if not self.config_store.save(self.settings):
            raise RuntimeError(self.config_store.last_error or tr("config.save_failed_unknown"))
        if not self.data_store.save(state):
            raise RuntimeError(self.data_store.last_error or tr("storage.save_failed_unknown"))
        self.analytics_store.replace_data(analytics)
        if self.analytics_store.last_error is not None:
            raise RuntimeError(self.analytics_store.last_error)
        self.session_manager = PomodoroSessionManager(self.data_store, self.analytics_store)
        self.metrics = self.session_manager.metrics()
        self.revlog_metrics_source = RevlogMetricsSource(self.mw)
        self._apply_revlog_metrics()
        self.timer.apply_settings(self.settings)
        self.timer.restore_state(self.session_manager.timer_state())
        self._last_timer_signature = None
        self._update_menu_text()
        self._rebuild_ui()
        self.update_visibility()

    def _reset_data(self, parent, reset_settings: bool) -> bool:
        title_key = "reset.all_confirm_title" if reset_settings else "reset.study_confirm_title"
        message_key = "reset.all_confirm" if reset_settings else "reset.study_confirm"
        if not _confirm_action(parent, tr(title_key), tr(message_key)):
            return False

        next_settings = PomodoroSettings() if reset_settings else self.settings
        audio_state = {} if reset_settings else self.ui.audio_state_snapshot()
        clean_state = _clean_state(next_settings, audio_state)

        try:
            self.ui.hide_floating_popovers()
            if reset_settings and not self.config_store.save(next_settings):
                raise RuntimeError(self.config_store.last_error or tr("config.save_failed_unknown"))
            if not self.data_store.save(clean_state):
                raise RuntimeError(self.data_store.last_error or tr("storage.save_failed_unknown"))
            self.analytics_store.replace_data({})
            if self.analytics_store.last_error is not None:
                raise RuntimeError(self.analytics_store.last_error)
        except Exception as exc:
            _show_warning(parent, tr("reset.error_title"), tr("reset.error", error=exc))
            return False

        self.settings = next_settings
        set_language(self.settings.language)
        self.tracker.on_reviewer_end()
        self.session_manager = PomodoroSessionManager(self.data_store, self.analytics_store)
        self.metrics = self.session_manager.metrics()
        self.revlog_metrics_source = RevlogMetricsSource(self.mw)
        self._apply_revlog_metrics()
        self._last_completed_metrics = None
        self._last_timer_signature = None
        self.timer.apply_settings(self.settings)
        self.timer.restore_state(self.session_manager.timer_state())
        self._update_menu_text()
        self._rebuild_ui()
        self.update_visibility()

        success_key = "reset.all_success" if reset_settings else "reset.study_success"
        _show_info(parent, tr("reset.success_title"), tr(success_key))
        return True

    def _rebuild_ui(self) -> None:
        self._apply_revlog_metrics()
        self.ui.rebuild(
            self.settings,
            self.metrics,
            self.experience_metrics,
            self.cards_metrics,
            self.retention_metrics,
            self.streak_metrics,
            self.study_time_metrics,
            self.session_manager.audio_state(),
        )
        self._sync_timer_state()
        self._mark_timer_started_if_running()

    def _warn_storage_failure_if_needed(self) -> None:
        analytics_error = getattr(getattr(self, "analytics_store", None), "last_error", None)
        if self.data_store.last_error is None and analytics_error is None:
            self._storage_warning_shown = False
            return
        if self._storage_warning_shown:
            return
        self._storage_warning_shown = True
        error = self.data_store.last_error or analytics_error
        _show_warning_message(tr("storage.save_failed", error=error))

    def _ensure_current_profile_bound(self) -> bool:
        if getattr(self.mw, "col", None) is None:
            return False
        current = self._current_profile_folder()
        if current and current != self._profile_folder:
            self.rebind_profile(self.mw)
        return True

    def _current_profile_folder(self) -> str:
        try:
            pm = getattr(self.mw, "pm", None)
            profile_folder_fn = getattr(pm, "profileFolder", None)
            if callable(profile_folder_fn):
                return str(profile_folder_fn() or "")
        except Exception:
            pass
        return ""

    def _current_profile_name(self) -> str:
        try:
            pm = getattr(self.mw, "pm", None)
            for attr in ("name", "profile_name", "profileName"):
                value = getattr(pm, attr, None)
                if value:
                    return str(value)
        except Exception:
            pass
        return ""

    def _log_profile_event(self, event: str) -> None:
        try:
            folder = self._current_profile_folder()
            if folder:
                log_path = Path(folder) / "pomodoro_qt.log"
            else:
                data_path = getattr(getattr(self, "data_store", None), "path", Path(__file__))
                log_path = Path(data_path).with_name("pomodoro_qt.log")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            data_path = getattr(getattr(self, "data_store", None), "path", "")
            analytics_path = getattr(getattr(self, "analytics_store", None), "path", "")
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    f"{timestamp} controller.{event}: "
                    f"profile_name={self._current_profile_name()!r}; "
                    f"profile_folder={folder!r}; "
                    f"data_store.path={str(data_path)!r}; "
                    f"analytics_store.path={str(analytics_path)!r}\n"
                )
        except Exception:
            pass

    def _warn_config_failure_if_needed(self) -> None:
        if self.config_store.last_error is None:
            self._config_warning_shown = False
            return
        if self._config_warning_shown:
            return
        self._config_warning_shown = True
        _show_warning_message(tr("config.save_failed", error=self.config_store.last_error))


_controller: Optional[PomodoroAddonController] = None
_profile_open_hook_registered = False


def setup_addon(addon_package: str) -> None:
    try:
        from aqt import gui_hooks
    except Exception:
        return
    global _profile_open_hook_registered

    def start_controller(*args) -> None:
        global _controller
        try:
            import aqt

            mw = getattr(aqt, "mw", None)
            if mw is None or getattr(mw, "col", None) is None:
                return
            if _controller is not None:
                _controller.rebind_profile(mw)
                return
            _controller = PomodoroAddonController(mw, addon_package)
            _controller.setup()
        except Exception as exc:
            try:
                from aqt.utils import showWarning

                showWarning(tr("error.initialize_failed", error=exc))
            except Exception:
                raise

    if not _profile_open_hook_registered and hasattr(gui_hooks, "profile_did_open"):
        gui_hooks.profile_did_open.append(start_controller)
        _profile_open_hook_registered = True

    QTimer.singleShot(0, start_controller)


def _dialog_accepted(dialog: QDialog) -> bool:
    result = dialog.exec()
    return _enum_value(result) == _enum_value(ACCEPTED)


def _clean_state(settings: PomodoroSettings, audio_state: dict) -> dict:
    state = default_state()
    state["timer_state"] = _fresh_timer_state(settings).to_dict()
    state["audio_state"] = dict(audio_state or {})
    return state


def _fresh_timer_state(settings: PomodoroSettings) -> TimerRuntimeState:
    total_seconds = max(1, int(settings.pomodoro_minutes)) * 60
    return TimerRuntimeState(
        mode=MODE_POMODORO,
        total_seconds=total_seconds,
        time_left=total_seconds,
        paused=True,
        started=False,
        saved_at="",
    )


def _confirm_action(parent, title: str, text: str) -> bool:
    buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    result = QMessageBox.question(parent, title, text, buttons, QMessageBox.StandardButton.No)
    return _enum_value(result) == _enum_value(QMessageBox.StandardButton.Yes)


def _show_info(parent, title: str, text: str) -> None:
    QMessageBox.information(parent, title, text)


def _show_warning(parent, title: str, text: str) -> None:
    QMessageBox.warning(parent, title, text)


def _show_warning_message(text: str) -> None:
    try:
        from aqt.utils import showWarning

        showWarning(text)
    except Exception:
        pass


def _enum_value(value) -> int:
    return int(value.value) if hasattr(value, "value") else int(value)
