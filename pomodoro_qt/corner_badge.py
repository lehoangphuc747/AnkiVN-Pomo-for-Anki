"""HTML/CSS backed Corner Badge layout."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Optional

from aqt.qt import QColor, QFrame, QHBoxLayout, QPoint, QTimer, Qt, pyqtSignal

from .i18n import current_language, tr
from .models import PomodoroTimerState, SessionMetrics


ASSET_DIR = Path(__file__).resolve().parent.parent / "web"
BRIDGE_PREFIX = "pomodoro:"


class HtmlCornerBadgeWidget(QFrame):
    """Corner badge rendered by local HTML/CSS while Python owns state."""

    action_requested = pyqtSignal(str)
    moved = pyqtSignal(int, int)

    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__()
        self.metrics = metrics
        self._saved_position: Optional[QPoint] = None
        self._drag_origin: Optional[QPoint] = None
        self._ready = False
        self._last_state: Optional[PomodoroTimerState] = None
        self._expanded_audio = False

        self.setObjectName("HtmlCornerBadgeWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(210, 286)

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

    def sync_state(self, state: PomodoroTimerState) -> None:
        self._last_state = state
        self._send_state()

    def refresh_metrics(self, metrics: SessionMetrics) -> None:
        self.metrics = metrics
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
        self.setFixedSize(210, 486 if expanded else 286)
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
        values = {
            "html_lang": current_language(),
            "corner_aria": tr("corner.aria"),
            "tooltip_drag_corner": tr("tooltip.drag_corner"),
            "mode_pomodoro": tr("mode.pomodoro"),
            "level_short": tr("metric.level_short"),
            "tooltip_pause_resume": tr("tooltip.pause_resume"),
            "tooltip_stop": tr("tooltip.stop"),
            "tooltip_sound": tr("tooltip.sound"),
            "tooltip_settings": tr("tooltip.settings"),
            "audio_title_lofi": tr("audio.title_lofi"),
            "audio_source_chillhop": tr("audio.source_chillhop"),
            "audio_youtube_placeholder": tr("audio.youtube_placeholder"),
            "action_load": tr("action.load"),
            "audio_inline_support": tr("audio.inline_support"),
            "streak_initial": tr("metric.day_short", count=0),
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
        mode_label = tr("mode.break_time") if state.mode == "break" else tr("mode.pomodoro")
        payload = {
            "mode": state.mode,
            "label": mode_label,
            "timeText": state.time_text,
            "progress": state.progress,
            "accent": state.accent,
            "paused": state.paused,
            "started": state.started,
            "streakText": tr("metric.day_short", count=metrics.streak_days),
            "labels": {
                "levelShort": tr("metric.level_short"),
                "pomodoro": tr("mode.pomodoro"),
            },
            "metrics": {
                "sessionIndex": metrics.session_index,
                "sessionTotal": metrics.session_total,
                "xpCurrent": metrics.xp_current,
                "xpGoal": metrics.xp_goal,
                "totalXp": metrics.total_xp,
                "level": metrics.level,
                "nextLevelXp": metrics.next_level_xp,
                "levelProgress": metrics.level_progress,
                "cards": metrics.cards,
                "retention": metrics.retention,
                "streakDays": metrics.streak_days,
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
