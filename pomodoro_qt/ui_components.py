"""Reusable Qt UI components for Pomodoro layouts."""

from __future__ import annotations

from typing import Optional

from aqt.qt import QColor, QFrame, QLabel, QPainter, QPen, QPushButton, QWidget, Qt

from .i18n import tr
from .models import MODE_BREAK, PomodoroTimerState, SessionMetrics
from .style import COLORS


ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
ANTIALIAS = QPainter.RenderHint.Antialiasing
ROUND_CAP = Qt.PenCapStyle.RoundCap
WIDGET_NO_FOCUS = Qt.FocusPolicy.NoFocus

SYMBOL_PLAY = "▶"
SYMBOL_PAUSE = "⏸"
SYMBOL_STOP = "■"
SYMBOL_MUSIC = "♪"
SYMBOL_GEAR = "⚙"
SYMBOL_LIGHTNING = "⚡"
SYMBOL_CLOSE = "×"
SYMBOL_SKIP_BACK = "⏮"
SYMBOL_SKIP_FORWARD = "⏭"
SYMBOL_REPEAT = "↻"
SYMBOL_TOMATO = "🍅"
SYMBOL_BREAK = "☕"
SYMBOL_FIRE = "🔥"
SYMBOL_SPARKLE = "✨"


def make_label(text: str, role: Optional[str] = None) -> QLabel:
    label = QLabel(text)
    if role:
        label.setProperty("role", role)
    return label


def make_button(text: str = "", role: Optional[str] = None, tooltip: str = "") -> QPushButton:
    button = QPushButton(text)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setFocusPolicy(WIDGET_NO_FOCUS)
    if role:
        button.setProperty("role", role)
    if tooltip:
        button.setToolTip(tooltip)
    return button


def set_accent_property(widget: QWidget, color: str) -> None:
    widget.setStyleSheet(f"color: {color};")


def mode_label_text(state: PomodoroTimerState) -> str:
    prefix = SYMBOL_BREAK if state.mode == MODE_BREAK else SYMBOL_TOMATO
    text = tr("mode.break_time") if state.mode == MODE_BREAK else tr("mode.pomodoro")
    return f"{prefix} {text.upper()}"


def make_toolbar_icon_button(symbol: str, tooltip: str, color: str = COLORS["muted"], font_size: int = 16) -> QPushButton:
    button = make_button(symbol, "toolbarIcon", tooltip)
    button.setFixedSize(28, 28)
    button.setStyleSheet(_icon_button_style(color, font_size))
    return button


def make_stop_button(color: str = COLORS["muted"], font_size: int = 14) -> QPushButton:
    return make_toolbar_icon_button(SYMBOL_STOP, tr("tooltip.stop"), color, font_size)


def make_sound_button(color: str = COLORS["muted"], font_size: int = 17) -> QPushButton:
    return make_toolbar_icon_button(SYMBOL_MUSIC, tr("tooltip.sound"), color, font_size)


def make_settings_button(color: str = COLORS["muted_light"], font_size: int = 16) -> QPushButton:
    return make_toolbar_icon_button(SYMBOL_GEAR, tr("tooltip.settings"), color, font_size)


def make_pause_button(color: str = COLORS["muted"], font_size: int = 16) -> QPushButton:
    return make_toolbar_icon_button(SYMBOL_PLAY, tr("tooltip.pause_resume"), color, font_size)


def make_primary_pause_button() -> QPushButton:
    button = make_button(SYMBOL_PLAY, "primaryPause", tr("tooltip.pause_resume"))
    button.setFixedSize(50, 36)
    button.setStyleSheet(_primary_pause_style())
    return button


def set_pause_button_state(button: QPushButton, paused: bool, primary: bool = False) -> None:
    button.setText(SYMBOL_PLAY if paused else SYMBOL_PAUSE)
    if primary:
        button.setStyleSheet(_primary_pause_style())
    else:
        button.setStyleSheet(_icon_button_style(COLORS["muted"], 16))


def make_pill_button(text: str, tooltip: str = "") -> QPushButton:
    button = make_button(text, "pill", tooltip)
    return button


def make_toolbar_metric_button(text: str, color: str, tooltip: str = "", weight: int = 600) -> QPushButton:
    button = make_button(text, "toolbarMetric", tooltip)
    button.setStyleSheet(
        f"""
        QPushButton {{
            color: {color};
            background: transparent;
            border: 0;
            border-radius: 999px;
            padding: 2px 6px;
            font-size: 12px;
            font-weight: {weight};
        }}
        QPushButton:hover {{
            background: {COLORS['soft']};
            border-radius: 999px;
        }}
        """
    )
    return button


def set_toolbar_metric_style(button: QPushButton, color: str, weight: int = 600) -> None:
    button.setStyleSheet(
        f"""
        QPushButton {{
            color: {color};
            background: transparent;
            border: 0;
            border-radius: 999px;
            padding: 2px 6px;
            font-size: 12px;
            font-weight: {weight};
        }}
        QPushButton:hover {{
            background: {COLORS['soft']};
            border-radius: 999px;
        }}
        """
    )


def make_session_dots_text(metrics: SessionMetrics) -> str:
    done = max(0, min(metrics.session_index, metrics.session_total))
    remaining = max(0, metrics.session_total - done)
    return f"{'● ' * done}{'○ ' * remaining} {metrics.session_index}/{metrics.session_total}".strip()


def make_sidebar_metric_button(label: str, value: str, tooltip: str = "") -> QPushButton:
    button = make_button(f"{label:<14}{value}", "metric", tooltip)
    button.setStyleSheet(
        f"""
        QPushButton {{
            color: {COLORS['text']};
            background: transparent;
            border: 0;
            border-radius: 12px;
            padding: 6px 8px;
            font-size: 13px;
            text-align: left;
        }}
        QPushButton:hover {{
            background: {COLORS['soft']};
            border-radius: 12px;
        }}
        """
    )
    return button


def make_audio_mini_button(text: str) -> QPushButton:
    button = make_button(f"{SYMBOL_MUSIC}  {text}", "audioMini", tr("tooltip.sound"))
    button.setStyleSheet(
        """
        QPushButton {
            background: #F2F1EC;
            color: #595752;
            border: 0;
            border-radius: 12px;
            padding: 10px 12px;
            font-size: 11px;
            font-weight: 600;
            text-align: left;
        }
        QPushButton:hover {
            background: #EAE8E2;
            border-radius: 12px;
        }
        """
    )
    return button


def _icon_button_style(color: str, font_size: int) -> str:
    return f"""
    QPushButton {{
        color: {color};
        background: transparent;
        border: 0;
        border-radius: 8px;
        font-size: {font_size}px;
        font-weight: 700;
        padding: 0;
    }}
    QPushButton:hover {{
        color: {COLORS['text']};
        background: transparent;
        border-radius: 8px;
    }}
    """


def _primary_pause_style() -> str:
    return f"""
    QPushButton {{
        background: {COLORS['red']};
        color: white;
        border: 0;
        border-radius: 10px;
        font-size: 16px;
        font-weight: 700;
        padding: 0;
    }}
    QPushButton:hover {{
        background: {COLORS['red_dark']};
        border-radius: 10px;
    }}
    """


class CircularProgress(QFrame):
    def __init__(self, diameter: int, line_width: int = 6, show_text: bool = True) -> None:
        super().__init__()
        self._progress = 1.0
        self._accent = COLORS["red"]
        self._text = "25:00"
        self._line_width = line_width
        self._show_text = show_text
        self.setFixedSize(diameter, diameter)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_state(self, state: PomodoroTimerState) -> None:
        self._progress = state.progress
        self._accent = state.accent
        self._text = state.time_text
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(ANTIALIAS)

        margin = self._line_width + 4
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        pen_bg = QPen(QColor("#EFECE5"), self._line_width)
        pen_bg.setCapStyle(ROUND_CAP)
        painter.setPen(pen_bg)
        painter.drawEllipse(rect)

        pen_progress = QPen(QColor(self._accent), self._line_width)
        pen_progress.setCapStyle(ROUND_CAP)
        painter.setPen(pen_progress)
        painter.drawArc(rect, 90 * 16, int(-360 * 16 * self._progress))

        if not self._show_text:
            return

        painter.setPen(QColor(COLORS["text"]))
        font = painter.font()
        font.setPointSize(22)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect().adjusted(0, 10, 0, -8), ALIGN_CENTER, self._text)
