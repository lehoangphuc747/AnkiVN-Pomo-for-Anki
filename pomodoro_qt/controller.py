"""Anki integration and layout orchestration for the Pomodoro Qt UI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from aqt.qt import QAction, QDialog, QDockWidget, QFileDialog, QMessageBox, QTimer, QWidget, Qt

from .backup import BackupError, build_backup, read_backup, write_backup
from .cards_studied import make_cards_studied_popover
from .config_store import ConfigStore
from .corner_badge import HtmlCornerBadgeWidget
from .dialogs import PomodoroDoneDialog
from .experience import make_experience_popover
from .i18n import set_language, tr
from .models import LAYOUT_CORNER, LAYOUT_SIDEBAR, LAYOUT_UNDER, MODE_POMODORO, SessionMetrics
from .retention import make_retention_popover
from .session_history import make_session_history_popover
from .session_manager import PomodoroSessionManager
from .settings_dialog import SettingsDialog
from .sidebar_panel import SidebarWidget
from .sound import AudioPopover
from .streaks import make_streak_popover
from .storage import PomodoroDataStore
from .style import addon_qss
from .timer import PomodoroTimer
from .tracking import ReviewTracker
from .under_toolbar import UnderToolbarWidget


TOP_DOCK = Qt.DockWidgetArea.TopDockWidgetArea
LEFT_DOCK = Qt.DockWidgetArea.LeftDockWidgetArea
NO_DOCK_FEATURES = QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
ACCEPTED = QDialog.DialogCode.Accepted
UNDER_TOOLBAR_STATES = {"deckBrowser", "overview", "review"}


class PomodoroAddonController:
    def __init__(self, mw, addon_package: str) -> None:
        self.mw = mw
        self.addon_package = addon_package
        self.config_store = ConfigStore(mw, addon_package)
        self.settings = self.config_store.load()
        set_language(self.settings.language)
        self.data_store = PomodoroDataStore(mw, addon_package)
        self.session_manager = PomodoroSessionManager(self.data_store)
        self.metrics = self.session_manager.metrics()
        self.timer = PomodoroTimer(self.settings)
        self.timer.restore_state(self.session_manager.timer_state())
        self.tracker = ReviewTracker(self._on_review_answered, self._deck_name_for_id)

        self.under_widget: Optional[UnderToolbarWidget] = None
        self.sidebar_widget: Optional[SidebarWidget] = None
        self.corner_widget: Optional[HtmlCornerBadgeWidget] = None
        self.under_dock: Optional[QDockWidget] = None
        self.sidebar_dock: Optional[QDockWidget] = None
        self.audio_popover: Optional[AudioPopover] = None
        self.metric_popovers = {}
        self._visible_metric_name: Optional[str] = None
        self._visible_metric_anchor: Optional[QWidget] = None
        self._last_completed_metrics: Optional[SessionMetrics] = None
        self._last_timer_signature = None
        self.settings_action: Optional[QAction] = None
        self._setup_done = False

    def setup(self) -> None:
        if self._setup_done:
            return
        self._setup_done = True
        self._build_ui()
        self._connect_timer()
        self._add_menu_action()
        self._install_hooks()
        QTimer.singleShot(0, self.update_visibility)

    def update_visibility(self) -> None:
        self._hide_all_layouts()

        shown_layout = False
        if self.settings.layout == LAYOUT_UNDER:
            if self._is_under_toolbar_state():
                if self.under_dock:
                    self.under_dock.show()
                shown_layout = True
            if not shown_layout:
                self._hide_floating_popovers()
            else:
                self._hide_popovers_if_anchor_hidden()
            return

        if self.settings.layout == LAYOUT_SIDEBAR:
            if self._is_review_state() and self.sidebar_dock:
                self.sidebar_dock.show()
                shown_layout = True
            if not shown_layout:
                self._hide_floating_popovers()
            else:
                self._hide_popovers_if_anchor_hidden()
            return

        if self.settings.layout == LAYOUT_CORNER:
            if self._is_review_state():
                self._attach_corner_to_reviewer()
            if self._is_review_state() and self.corner_widget:
                self.corner_widget.show()
                self.corner_widget.raise_()
                shown_layout = True
            if not shown_layout:
                self._hide_floating_popovers()
            else:
                self._hide_popovers_if_anchor_hidden()
            return

        self._hide_floating_popovers()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.mw, self.settings)
        dialog.setStyleSheet(addon_qss())
        dialog.export_requested.connect(lambda: self._export_backup(dialog))
        dialog.import_requested.connect(lambda: self._import_backup(dialog))
        if _dialog_accepted(dialog):
            self._save_runtime_state()
            self.settings = dialog.to_settings(self.settings)
            set_language(self.settings.language)
            self.config_store.save(self.settings)
            self.timer.apply_settings(self.settings)
            self._update_menu_text()
            self._rebuild_ui()
            self.update_visibility()

    def _export_backup(self, parent: QWidget) -> None:
        self._save_runtime_state()
        file_path = _save_file_name(
            parent,
            tr("backup.export_title"),
            self._default_backup_path(),
            tr("backup.file_filter"),
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".json"):
            file_path = f"{file_path}.json"
        try:
            payload = build_backup(self.settings, self.data_store.load())
            write_backup(file_path, payload)
        except Exception as exc:
            _show_warning(parent, tr("backup.export_error_title"), tr("backup.export_error", error=exc))
            return
        _show_info(parent, tr("backup.export_success_title"), tr("backup.export_success", path=file_path))

    def _import_backup(self, dialog: SettingsDialog) -> None:
        file_path = _open_file_name(dialog, tr("backup.import_title"), "", tr("backup.file_filter"))
        if not file_path:
            return
        try:
            imported_settings, imported_state = read_backup(file_path)
        except BackupError as exc:
            _show_warning(dialog, tr("backup.import_error_title"), tr("backup.import_error", error=tr(exc.key)))
            return
        except Exception as exc:
            _show_warning(dialog, tr("backup.import_error_title"), tr("backup.import_error", error=exc))
            return
        if not _confirm_replace(dialog):
            return
        try:
            self._apply_imported_backup(imported_settings, imported_state)
        except Exception as exc:
            _show_warning(dialog, tr("backup.import_error_title"), tr("backup.import_error", error=exc))
            return
        _show_info(dialog, tr("backup.import_success_title"), tr("backup.import_success"))
        dialog.reject()

    def _apply_imported_backup(self, settings, state: dict) -> None:
        self._hide_floating_popovers()
        self.settings = settings
        set_language(self.settings.language)
        self.config_store.save(self.settings)
        self.data_store.save(state)
        self.session_manager = PomodoroSessionManager(self.data_store)
        self.metrics = self.session_manager.metrics()
        self.timer.apply_settings(self.settings)
        self.timer.restore_state(self.session_manager.timer_state())
        self._last_timer_signature = None
        self._update_menu_text()
        self._rebuild_ui()
        self.update_visibility()

    def _default_backup_path(self) -> str:
        filename = datetime.now().strftime("pomodoro-backup-%Y%m%d-%H%M%S.json")
        return str(Path.home() / filename)

    def _build_ui(self) -> None:
        self.under_widget = UnderToolbarWidget(self.metrics)
        self.sidebar_widget = SidebarWidget(self.metrics)
        self.corner_widget = HtmlCornerBadgeWidget(self.metrics)
        self.audio_popover = AudioPopover()
        self.audio_popover.restore_state(self.session_manager.audio_state())
        self.metric_popovers = self._make_metric_popovers()

        for widget in [
            self.under_widget,
            self.sidebar_widget,
            self.audio_popover,
            *self.metric_popovers.values(),
        ]:
            widget.setStyleSheet(addon_qss())

        self.under_dock = self._make_dock("PomodoroUnderToolbar", self.under_widget, TOP_DOCK)
        self.sidebar_dock = self._make_dock("PomodoroSidebar", self.sidebar_widget, LEFT_DOCK)
        self.corner_widget.set_saved_position(self.settings.corner_left, self.settings.corner_top)

        self._connect_layout_buttons(self.under_widget, floating_audio=True)
        self._connect_layout_buttons(self.sidebar_widget, floating_audio=True)
        self.corner_widget.action_requested.connect(self._handle_corner_action)
        self.corner_widget.moved.connect(self._save_corner_position)

        self._sync_timer_state()
        self._mark_timer_started_if_running()

    def _make_dock(self, object_name: str, widget: QWidget, area) -> QDockWidget:
        dock = QDockWidget("", self.mw)
        dock.setObjectName(object_name)
        dock.setWidget(widget)
        dock.setFeatures(NO_DOCK_FEATURES)
        dock.setAllowedAreas(area)
        dock.setTitleBarWidget(QWidget(dock))
        dock.setStyleSheet(addon_qss())
        self.mw.addDockWidget(area, dock)
        dock.hide()
        return dock

    def _connect_timer(self) -> None:
        self.timer.changed.connect(self._sync_timer_state)
        self.timer.pomodoro_completed.connect(self._on_pomodoro_completed)
        self.timer.break_completed.connect(self._on_break_completed)
        self.timer.pomodoro_done.connect(self._show_done_dialog)

    def _connect_layout_buttons(self, widget, floating_audio: bool) -> None:
        widget.pause_button.clicked.connect(self._toggle_timer_pause)
        widget.stop_button.clicked.connect(self._stop_timer)
        widget.settings_button.clicked.connect(self.open_settings)

        if floating_audio:
            widget.audio_button.clicked.connect(lambda _checked=False, button=widget.audio_button: self._toggle_audio(button))

        widget.session_button.clicked.connect(lambda _checked=False, button=widget.session_button: self._show_metric("session", button))
        widget.experience_button.clicked.connect(lambda _checked=False, button=widget.experience_button: self._show_metric("experience", button))
        widget.cards_button.clicked.connect(lambda _checked=False, button=widget.cards_button: self._show_metric("cards", button))
        widget.streak_button.clicked.connect(lambda _checked=False, button=widget.streak_button: self._show_metric("streak", button))
        if hasattr(widget, "retention_button"):
            widget.retention_button.clicked.connect(
                lambda _checked=False, button=widget.retention_button: self._show_metric("retention", button)
            )

    def _add_menu_action(self) -> None:
        menu = getattr(getattr(self.mw, "form", None), "menuTools", None)
        if menu is None:
            return
        action = QAction(tr("menu.settings"), self.mw)
        action.triggered.connect(self.open_settings)
        menu.addAction(action)
        self.settings_action = action

    def _update_menu_text(self) -> None:
        if self.settings_action is not None:
            self.settings_action.setText(tr("menu.settings"))

    def _rebuild_ui(self) -> None:
        self._dispose_ui()
        self._build_ui()

    def _dispose_ui(self) -> None:
        self._hide_floating_popovers()

        if self.under_dock is not None:
            self.mw.removeDockWidget(self.under_dock)
            self.under_dock.deleteLater()
        if self.sidebar_dock is not None:
            self.mw.removeDockWidget(self.sidebar_dock)
            self.sidebar_dock.deleteLater()
        if self.corner_widget is not None:
            self.corner_widget.hide()
            self.corner_widget.setParent(None)
            self.corner_widget.deleteLater()
        if self.audio_popover is not None:
            self.audio_popover.hide()
            self.audio_popover.deleteLater()
        for popover in self.metric_popovers.values():
            popover.hide()
            popover.deleteLater()

        self.under_widget = None
        self.sidebar_widget = None
        self.corner_widget = None
        self.under_dock = None
        self.sidebar_dock = None
        self.audio_popover = None
        self.metric_popovers = {}
        self._visible_metric_name = None
        self._visible_metric_anchor = None

    def _install_hooks(self) -> None:
        try:
            from aqt import gui_hooks
        except Exception:
            return

        self._append_hook(gui_hooks, "state_did_change", self._on_anki_state_changed)
        self._append_hook(gui_hooks, "reviewer_did_show_question", self._on_reviewer_refreshed)
        self._append_hook(gui_hooks, "reviewer_did_show_answer", self._on_reviewer_refreshed)
        self._append_hook(gui_hooks, "reviewer_will_answer_card", self.tracker.on_pre_answer)
        self._append_hook(gui_hooks, "reviewer_did_answer_card", self.tracker.on_did_answer)
        self._append_hook(gui_hooks, "reviewer_will_end", self.tracker.on_reviewer_end)
        self._append_hook(gui_hooks, "profile_will_close", self._on_profile_will_close)

    def _append_hook(self, gui_hooks, name: str, callback) -> None:
        hook = getattr(gui_hooks, name, None)
        if hook is None:
            return
        try:
            hook.append(callback)
        except Exception:
            pass

    def _on_anki_state_changed(self, *args) -> None:
        QTimer.singleShot(0, self.update_visibility)

    def _on_reviewer_refreshed(self, *args) -> None:
        QTimer.singleShot(0, self.update_visibility)

    def _on_profile_will_close(self, *args) -> None:
        self._save_runtime_state()
        self._hide_all_layouts()

    def _sync_timer_state(self, *args) -> None:
        state = self.timer.state()
        for widget in [self.under_widget, self.sidebar_widget, self.corner_widget]:
            if widget:
                widget.sync_state(state)
        signature = (state.mode, state.total_seconds, state.paused)
        if self._last_timer_signature is not None and signature != self._last_timer_signature:
            self.session_manager.save_timer_state(self.timer.runtime_state())
        self._last_timer_signature = signature

    def _toggle_timer_pause(self) -> None:
        self.timer.toggle_pause()
        if not self.timer.paused:
            self.metrics = self.session_manager.mark_timer_started()
            self._refresh_metrics()
        self.session_manager.save_timer_state(self.timer.runtime_state())

    def _stop_timer(self) -> None:
        duration_seconds = max(0, self.timer.total_seconds - self.timer.time_left)
        self.metrics = self.session_manager.stop_current_session(self.timer.mode, duration_seconds)
        self.timer.stop()
        self.session_manager.save_timer_state(self.timer.runtime_state())
        self._refresh_metrics()

    def _on_pomodoro_completed(self) -> None:
        self._last_completed_metrics = self.session_manager.complete_pomodoro(self.timer.total_seconds)
        self.metrics = self.session_manager.metrics()
        self._refresh_metrics()

    def _on_break_completed(self) -> None:
        self.metrics = self.session_manager.complete_break(self.timer.total_seconds)
        self._refresh_metrics()
        QTimer.singleShot(0, self._mark_timer_started_if_running)

    def _show_done_dialog(self) -> None:
        dialog = PomodoroDoneDialog(self.mw, self.settings, self._last_completed_metrics or self.metrics)
        dialog.setStyleSheet(addon_qss())
        if _dialog_accepted(dialog):
            self.timer.start_mode(dialog.choice)
            if dialog.choice == MODE_POMODORO:
                self._mark_timer_started_if_running()
            self.session_manager.save_timer_state(self.timer.runtime_state())

    def _show_metric(self, name: str, anchor: QWidget) -> None:
        popover = self.metric_popovers.get(name)
        if popover is None:
            return
        if popover.isVisible():
            popover.hide()
            self._visible_metric_name = None
            self._visible_metric_anchor = None
            return
        for key, other_popover in self.metric_popovers.items():
            if key != name:
                other_popover.hide()
        popover = self._replace_metric_popover(name)
        if popover is None:
            return
        self._visible_metric_name = name
        self._visible_metric_anchor = anchor
        popover.show_at(anchor)

    def _toggle_audio(self, anchor: QWidget) -> None:
        if self.audio_popover:
            self.audio_popover.toggle_at(anchor)

    def _handle_corner_action(self, action: str) -> None:
        if action == "pause":
            self._toggle_timer_pause()
            return
        if action == "stop":
            self._stop_timer()
            return
        if action == "settings":
            self.open_settings()
            return
        if action in {"session", "experience", "cards", "streak", "retention"} and self.corner_widget:
            self._show_metric(action, self.corner_widget)

    def _save_corner_position(self, left: int, top: int) -> None:
        self.settings.corner_left = left
        self.settings.corner_top = top
        self.config_store.save(self.settings)

    def _on_review_answered(self, event) -> None:
        self.metrics = self.session_manager.record_answer(event)
        self._refresh_metrics()

    def _mark_timer_started_if_running(self) -> None:
        if self.timer.mode != MODE_POMODORO or self.timer.paused:
            return
        self.metrics = self.session_manager.mark_timer_started()
        self.session_manager.save_timer_state(self.timer.runtime_state())
        self._refresh_metrics()

    def _refresh_metrics(self) -> None:
        self.metrics = self.session_manager.metrics()
        for widget in [self.under_widget, self.sidebar_widget, self.corner_widget]:
            if widget:
                widget.refresh_metrics(self.metrics)
        self._refresh_visible_metric_popover()

    def _make_metric_popovers(self) -> dict:
        popovers = {}
        for name in ["session", "experience", "cards", "retention", "streak"]:
            popover = self._make_metric_popover(name)
            if popover is not None:
                popovers[name] = popover
        return popovers

    def _make_metric_popover(self, name: str):
        if name == "session":
            return make_session_history_popover(self.metrics, self.session_manager.today_history())
        if name == "experience":
            return make_experience_popover(self.metrics)
        if name == "cards":
            return make_cards_studied_popover(self.metrics)
        if name == "retention":
            return make_retention_popover(self.metrics)
        if name == "streak":
            return make_streak_popover(self.metrics)
        return None

    def _replace_metric_popover(self, name: str):
        old_popover = self.metric_popovers.get(name)
        if old_popover is not None:
            old_popover.hide()
            old_popover.deleteLater()
        popover = self._make_metric_popover(name)
        if popover is None:
            self.metric_popovers.pop(name, None)
            return None
        popover.setStyleSheet(addon_qss())
        self.metric_popovers[name] = popover
        return popover

    def _refresh_visible_metric_popover(self) -> None:
        name = self._visible_metric_name
        anchor = self._visible_metric_anchor
        if not name or anchor is None or not anchor.isVisible():
            return
        popover = self.metric_popovers.get(name)
        if popover is None or not popover.isVisible():
            return
        refreshed = self._replace_metric_popover(name)
        if refreshed is not None:
            refreshed.show_at(anchor)

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
        if self.audio_popover:
            self.session_manager.save_audio_state(self.audio_popover.state_snapshot())
        self.session_manager.save_timer_state(self.timer.runtime_state())

    def _hide_all_layouts(self) -> None:
        if self.under_dock:
            self.under_dock.hide()
        if self.sidebar_dock:
            self.sidebar_dock.hide()
        if self.corner_widget:
            self.corner_widget.hide()

    def _hide_popovers_if_anchor_hidden(self) -> None:
        if self.audio_popover and self.audio_popover.isVisible() and not self.audio_popover.anchor_is_visible():
            self.audio_popover.hide()

        anchor = self._visible_metric_anchor
        if anchor is None or anchor.isVisible():
            return
        self._hide_metric_popovers()

    def _hide_floating_popovers(self) -> None:
        if self.audio_popover:
            self.audio_popover.hide()
        self._hide_metric_popovers()

    def _hide_metric_popovers(self) -> None:
        for popover in self.metric_popovers.values():
            popover.hide()
        self._visible_metric_name = None
        self._visible_metric_anchor = None

    def _is_under_toolbar_state(self) -> bool:
        return getattr(self.mw, "state", None) in UNDER_TOOLBAR_STATES

    def _is_review_state(self) -> bool:
        return getattr(self.mw, "state", None) == "review"

    def _attach_corner_to_reviewer(self) -> None:
        if not self.corner_widget:
            return
        parent = self._reviewer_parent()
        if parent is None:
            return
        if self.corner_widget.parentWidget() is not parent:
            self.corner_widget.setParent(parent)
            self.corner_widget.setStyleSheet(addon_qss())
            self.corner_widget.set_saved_position(self.settings.corner_left, self.settings.corner_top)
        self.corner_widget.raise_()

    def _reviewer_parent(self) -> Optional[QWidget]:
        reviewer = getattr(self.mw, "reviewer", None)
        web = getattr(reviewer, "web", None)
        if web is not None:
            parent = web.parentWidget()
            if parent is not None:
                return parent
            return web
        return self.mw.centralWidget()


_controller: Optional[PomodoroAddonController] = None


def setup_addon(addon_package: str) -> None:
    try:
        from aqt import gui_hooks
    except Exception:
        return

    def start_controller(*args) -> None:
        global _controller
        if _controller is not None:
            return
        try:
            import aqt

            mw = getattr(aqt, "mw", None)
            if mw is None:
                return
            _controller = PomodoroAddonController(mw, addon_package)
            _controller.setup()
        except Exception as exc:
            try:
                from aqt.utils import showWarning

                showWarning(tr("error.initialize_failed", error=exc))
            except Exception:
                raise

    if hasattr(gui_hooks, "profile_did_open"):
        gui_hooks.profile_did_open.append(start_controller)

    QTimer.singleShot(0, start_controller)


def _dialog_accepted(dialog: QDialog) -> bool:
    result = dialog.exec()
    return _enum_value(result) == _enum_value(ACCEPTED)


def _save_file_name(parent: QWidget, title: str, default_path: str, file_filter: str) -> str:
    result = QFileDialog.getSaveFileName(parent, title, default_path, file_filter)
    return _dialog_path(result)


def _open_file_name(parent: QWidget, title: str, default_path: str, file_filter: str) -> str:
    result = QFileDialog.getOpenFileName(parent, title, default_path, file_filter)
    return _dialog_path(result)


def _dialog_path(result) -> str:
    if isinstance(result, tuple):
        return str(result[0] or "")
    return str(result or "")


def _confirm_replace(parent: QWidget) -> bool:
    buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    result = QMessageBox.question(
        parent,
        tr("backup.confirm_replace_title"),
        tr("backup.confirm_replace"),
        buttons,
        QMessageBox.StandardButton.No,
    )
    return _enum_value(result) == _enum_value(QMessageBox.StandardButton.Yes)


def _show_info(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.information(parent, title, text)


def _show_warning(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.warning(parent, title, text)


def _enum_value(value) -> int:
    return int(value.value) if hasattr(value, "value") else int(value)
