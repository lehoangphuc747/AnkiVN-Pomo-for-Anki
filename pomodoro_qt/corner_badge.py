"""HTML/CSS backed Corner Badge layout."""

from __future__ import annotations

import html
import base64
import json
from pathlib import Path
from typing import Optional

from aqt.qt import QColor, QFrame, QHBoxLayout, QPoint, QTimer, Qt, pyqtSignal

from .i18n import current_language, format_number, tr
from .cards_metric import CardsStudiedMetrics
from .experience_metric import ExperienceMetrics
from .models import PomodoroTimerState, SessionMetrics
from .retention_metric import RetentionMetrics
from .study_time_metric import StudyTimeMetrics, format_study_duration
from .streak_metric import StreakMetrics


ASSET_DIR = Path(__file__).resolve().parent.parent / "web"
ROOT_DIR = ASSET_DIR.parent
ICON_DIR = ROOT_DIR / "assets" / "icons"
BRIDGE_PREFIX = "pomodoro:"


class HtmlCornerBadgeWidget(QFrame):
    """Corner badge rendered by local HTML/CSS while Python owns state."""

    action_requested = pyqtSignal(str)
    moved = pyqtSignal(int, int)

    def __init__(
        self,
        metrics: SessionMetrics,
        experience_metrics: ExperienceMetrics,
        cards_metrics: CardsStudiedMetrics,
        retention_metrics: RetentionMetrics,
        streak_metrics: StreakMetrics,
        study_time_metrics: StudyTimeMetrics,
    ) -> None:
        super().__init__()
        self.metrics = metrics
        self.experience_metrics = experience_metrics
        self.cards_metrics = cards_metrics
        self.retention_metrics = retention_metrics
        self.streak_metrics = streak_metrics
        self.study_time_metrics = study_time_metrics
        self._saved_position: Optional[QPoint] = None
        self._drag_origin: Optional[QPoint] = None
        self._ready = False
        self._last_state: Optional[PomodoroTimerState] = None
        self._expanded_audio = False

        self.setObjectName("HtmlCornerBadgeWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._collapsed_height = 344
        self.setFixedSize(204, self._collapsed_height)

        self.web = self._make_webview()
        self.web.setObjectName("PomodoroCornerBadgeWeb")
        self.web.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.web.setStyleSheet("background: transparent; border: 0;")
        try:
            self.web.page().setBackgroundColor(QColor(0, 0, 0, 0))
        except Exception:
            pass

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.web)

        self._load_html()

    def set_saved_position(self, left: Optional[int], top: Optional[int]) -> None:
        if left is None or top is None:
            self._saved_position = None
            return
        self._saved_position = QPoint(left, top)

    def sync_state(self, state: PomodoroTimerState, study_time_metrics: StudyTimeMetrics | None = None) -> None:
        self._last_state = state
        if study_time_metrics is not None:
            self.study_time_metrics = study_time_metrics
        self._send_state()

    def refresh_metrics(
        self,
        metrics: SessionMetrics,
        experience_metrics: ExperienceMetrics,
        cards_metrics: CardsStudiedMetrics,
        retention_metrics: RetentionMetrics,
        streak_metrics: StreakMetrics,
        study_time_metrics: StudyTimeMetrics,
    ) -> None:
        self.metrics = metrics
        self.experience_metrics = experience_metrics
        self.cards_metrics = cards_metrics
        self.retention_metrics = retention_metrics
        self.streak_metrics = streak_metrics
        self.study_time_metrics = study_time_metrics
        self._send_state()

    def showEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().showEvent(event)
        if self._saved_position is not None:
            self._move_clamped(self._saved_position)
            return
        parent = self.parentWidget()
        if parent:
            self._move_clamped(QPoint(parent.width() - self.width() - 24, 24))

    def resize_for_audio(self, expanded: bool) -> None:
        self._expanded_audio = expanded
        self.setFixedSize(204, self._collapsed_height + (180 if expanded else 0))
        self._move_clamped(self.pos())

    def _make_webview(self):
        from aqt.webview import AnkiWebView

        web = AnkiWebView()
        try:
            web.set_bridge_command(self._handle_bridge, self)
        except TypeError:
            web.set_bridge_command(self._handle_bridge)
        if hasattr(web, "loadFinished"):
            web.loadFinished.connect(lambda _ok: self._on_loaded())
        return web

    def _load_html(self) -> None:
        template = (ASSET_DIR / "pomodoro_ui.html").read_text(encoding="utf-8")
        css = (ASSET_DIR / "pomodoro_ui.css").read_text(encoding="utf-8")
        js = (ASSET_DIR / "pomodoro_ui.js").read_text(encoding="utf-8")
        template = self._render_template(template)
        document = template.replace("/*__POMODORO_CSS__*/", css)
        document = document.replace("//__POMODORO_JS__", js)
        body = self._extract_body(template).replace("//__POMODORO_JS__", js)
        body = f"<style>{css}</style>{body}"
        try:
            self.web.stdHtml(body)
        except Exception:
            self.web.setHtml(document)
            QTimer.singleShot(250, self._on_loaded)

    def _extract_body(self, html: str) -> str:
        lower_html = html.lower()
        start = lower_html.find("<body>")
        end = lower_html.rfind("</body>")
        if start == -1 or end == -1:
            return html
        return html[start + len("<body>") : end]

    def _render_template(self, template: str) -> str:
        tomato_icon_src = _svg_data_uri(ICON_DIR / "tomato-1-svgrepo-com.svg")
        play_icon_src = _svg_data_uri(ICON_DIR / "flaticon_10264043.svg")
        pause_icon_src = _svg_data_uri(ICON_DIR / "pause-svgrepo-com.svg")
        stop_icon_src = _svg_data_uri(ICON_DIR / "stop-svgrepo-com.svg")
        shuffle_icon_src = _svg_data_uri(ICON_DIR / "shuffle-svgrepo-com.svg")
        previous_icon_src = _svg_data_uri(ICON_DIR / "previous-999-svgrepo-com.svg")
        next_icon_src = _svg_data_uri(ICON_DIR / "next-998-svgrepo-com.svg")
        loop_icon_src = _svg_data_uri(ICON_DIR / "loop-svgrepo-com.svg")
        settings_icon_src = _svg_data_uri(ICON_DIR / "settings-cog-options-config-configure-gear-engineering-svgrepo-com.svg")
        feedback_icon_src = _svg_data_uri(ICON_DIR / "question-svgrepo-com.svg")
        soundcloud_icon_src = _svg_data_uri(ICON_DIR / "soundcloud-sound-cloud-svgrepo-com.svg")
        bolt_icon_src = _svg_data_uri(ICON_DIR / "bolt-svgrepo-com.svg")
        growth_icon_src = _svg_data_uri(ICON_DIR / "level.svg")
        fire_icon_src = _svg_data_uri(ICON_DIR / "fire-svgrepo-com.svg")
        brain_icon_src = _svg_data_uri(ICON_DIR / "brain-svgrepo-com.svg")
        time_icon_src = _svg_data_uri(ICON_DIR / "time-clock-timer-appointment-svgrepo-com.svg")
        history_icon_src = _svg_data_uri(ICON_DIR / "history.svg")
        values = {
            "html_lang": current_language(),
            "corner_aria": tr("corner.aria"),
            "tooltip_drag_corner": tr("tooltip.drag_corner"),
            "tooltip_session_history": tr("tooltip.session_history"),
            "tooltip_study_time": tr("tooltip.study_time"),
            "mode_pomodoro": tr("mode.pomodoro"),
            "level_short": tr("metric.level_short"),
            "tooltip_pause_resume": tr("tooltip.pause_resume"),
            "tooltip_stop": tr("tooltip.stop"),
            "tooltip_sound": tr("tooltip.sound"),
            "tooltip_feedback": tr("tooltip.feedback"),
            "tooltip_settings": tr("tooltip.settings"),
            "audio_title_lofi": tr("audio.short_rain"),
            "audio_source_chillhop": tr("audio.source_dmk67"),
            "audio_youtube_placeholder": tr("audio.youtube_placeholder"),
            "action_load": tr("action.load"),
            "action_shuffle": tr("action.shuffle"),
            "action_previous": tr("action.previous"),
            "action_play": tr("action.play"),
            "action_next": tr("action.next"),
            "action_loop": tr("action.loop"),
            "audio_inline_support": tr("audio.inline_support"),
            "streak_initial": tr("metric.day_short", count=format_number(0)),
            "streak_caption_initial": tr("streak.status_start"),
            "tomato_icon_src": tomato_icon_src,
            "play_icon_src": play_icon_src,
            "pause_icon_src": pause_icon_src,
            "stop_icon_src": stop_icon_src,
            "shuffle_icon_src": shuffle_icon_src,
            "previous_icon_src": previous_icon_src,
            "next_icon_src": next_icon_src,
            "loop_icon_src": loop_icon_src,
            "settings_icon_src": settings_icon_src,
            "feedback_icon_src": feedback_icon_src,
            "soundcloud_icon_src": soundcloud_icon_src,
            "bolt_icon_src": bolt_icon_src,
            "growth_icon_src": growth_icon_src,
            "fire_icon_src": fire_icon_src,
            "brain_icon_src": brain_icon_src,
            "time_icon_src": time_icon_src,
            "history_icon_src": history_icon_src,
        }
        for key, value in values.items():
            template = template.replace("{{" + key + "}}", html.escape(str(value), quote=True))
        return template

    def _on_loaded(self) -> None:
        self._ready = True
        self._send_state()

    def _send_state(self) -> None:
        if not self._ready or self._last_state is None:
            return
        state = self._last_state
        metrics = self.metrics
        experience_metrics = self.experience_metrics
        cards_metrics = self.cards_metrics
        retention_metrics = self.retention_metrics
        streak_metrics = self.streak_metrics
        study_time_metrics = self.study_time_metrics
        mode_label = tr("mode.break_time") if state.mode == "break" else tr("mode.pomodoro")
        payload = {
            "mode": state.mode,
            "label": mode_label,
            "timeText": state.time_text,
            "progress": state.progress,
            "accent": state.accent,
            "paused": state.paused,
            "started": state.started,
            "streakText": tr("metric.day_short", count=format_number(streak_metrics.days)),
            "streakCaption": _streak_caption(streak_metrics),
            "labels": {
                "levelShort": tr("metric.level_short"),
                "pomodoro": tr("mode.pomodoro"),
                "streakCaption": tr("streak.status_start"),
            },
            "metrics": {
                "sessionIndex": metrics.session_index,
                "sessionTotal": metrics.session_total,
                "xpCurrent": experience_metrics.experience,
                "xpGoal": experience_metrics.next_level_experience,
                "totalXp": experience_metrics.experience,
                "level": experience_metrics.level,
                "nextLevelXp": experience_metrics.next_level_experience,
                "levelProgress": experience_metrics.level_progress,
                "cards": cards_metrics.cards,
                "retention": retention_metrics.today_retention,
                "streakDays": streak_metrics.days,
                "studyTimeToday": study_time_metrics.today_seconds,
                "studyTimeAllTime": study_time_metrics.all_time_seconds,
            },
            "metricsText": {
                "level": format_number(experience_metrics.level),
                "cards": format_number(cards_metrics.cards),
                "retention": tr("common.percent", value=format_number(retention_metrics.today_retention)),
                "streakDays": format_number(streak_metrics.days),
                "studyTime": format_study_duration(study_time_metrics.today_seconds),
            },
        }
        self._eval_js(f"window.PomodoroUI && window.PomodoroUI.update({json.dumps(payload)});")

    def _eval_js(self, js: str) -> None:
        try:
            self.web.eval(js)
        except Exception:
            try:
                self.web.page().runJavaScript(js)
            except Exception:
                pass

    def _handle_bridge(self, message: str) -> None:
        if not message.startswith(BRIDGE_PREFIX):
            return
        try:
            payload = json.loads(message[len(BRIDGE_PREFIX) :])
        except json.JSONDecodeError:
            return

        event_type = payload.get("type")
        if event_type == "ready":
            self._on_loaded()
            return
        if event_type == "dragStart":
            self._drag_origin = self.pos()
            return
        if event_type == "dragMove":
            if self._drag_origin is None:
                self._drag_origin = self.pos()
            dx = int(payload.get("dx") or 0)
            dy = int(payload.get("dy") or 0)
            self._move_clamped(self._drag_origin + QPoint(dx, dy))
            return
        if event_type == "dragEnd":
            self._drag_origin = None
            self.moved.emit(self.x(), self.y())
            return
        if event_type == "audioToggled":
            self.resize_for_audio(bool(payload.get("expanded")))
            return
        if event_type == "action":
            action = str(payload.get("action") or "")
            if action:
                self.action_requested.emit(action)

    def _move_clamped(self, point: QPoint) -> None:
        parent = self.parentWidget()
        if not parent:
            self.move(point)
            return
        left = max(16, min(point.x(), parent.width() - self.width() - 16))
        top = max(16, min(point.y(), parent.height() - self.height() - 16))
        self.move(left, top)


def _svg_data_uri(path: Path) -> str:
    content = path.read_bytes()
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _streak_caption(metrics: StreakMetrics) -> str:
    if metrics.today_reviews > 0:
        return tr("streak.status_kept")
    if metrics.days > 0:
        return tr("streak.status_need_today")
    return tr("streak.status_start")
