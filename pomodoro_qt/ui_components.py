"""Reusable Qt UI components for Pomodoro layouts."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from aqt.qt import QColor, QFrame, QHBoxLayout, QIcon, QLabel, QPainter, QPen, QPushButton, QSize, QVBoxLayout, QWidget, Qt, pyqtSignal

from .i18n import tr
from .models import MODE_BREAK, PomodoroTimerState, SessionMetrics
from .style import COLORS


ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
ANTIALIAS = QPainter.RenderHint.Antialiasing
ROUND_CAP = Qt.PenCapStyle.RoundCap
WIDGET_NO_FOCUS = Qt.FocusPolicy.NoFocus
ASSET_DIR = Path(__file__).resolve().parent.parent
ICON_DIR = ASSET_DIR / "assets" / "icons"
TOMATO_ICON_PATH = ICON_DIR / "tomato-1-svgrepo-com.svg"
TOMATO_COMPLETED_ICON_PATH = ICON_DIR / "tomato-svgrepo-com.svg"
TOMATO_INCOMPLETE_ICON_PATH = ICON_DIR / "tomato-svgrepo-com (1).svg"
ADDON_LOGO_PATH = TOMATO_ICON_PATH
BOLT_ICON_PATH = ICON_DIR / "bolt-svgrepo-com.svg"
GROWTH_ICON_PATH = ICON_DIR / "idea-svgrepo-com.svg"
FIRE_ICON_PATH = ICON_DIR / "fire-svgrepo-com.svg"
VIETNAM_ICON_PATH = ICON_DIR / "flag-for-vietnam-svgrepo-com.svg"
BRAIN_ICON_PATH = ICON_DIR / "brain-svgrepo-com.svg"
HISTORY_ICON_PATH = ICON_DIR / "history.svg"
PLAY_ICON_PATH = ICON_DIR / "flaticon_10264043.svg"
PAUSE_ICON_PATH = ICON_DIR / "pause-svgrepo-com.svg"
SOUNDCLOUD_ICON_PATH = ICON_DIR / "soundcloud-sound-cloud-svgrepo-com.svg"
STOP_ICON_PATH = ICON_DIR / "stop-svgrepo-com.svg"
SHUFFLE_ICON_PATH = ICON_DIR / "shuffle-svgrepo-com.svg"
PREVIOUS_ICON_PATH = ICON_DIR / "previous-999-svgrepo-com.svg"
NEXT_ICON_PATH = ICON_DIR / "next-998-svgrepo-com.svg"
LOOP_ICON_PATH = ICON_DIR / "loop-svgrepo-com.svg"
SETTINGS_ICON_PATH = ICON_DIR / "settings-cog-options-config-configure-gear-engineering-svgrepo-com.svg"
RED_CIRCLE_ICON_PATH = ICON_DIR / "red-circle-svgrepo-com.svg"
BLACK_CIRCLE_ICON_PATH = ICON_DIR / "black-circle-svgrepo-com.svg"

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
SYMBOL_SPARKLE = "✨"


def make_label(text: str, role: Optional[str] = None) -> QLabel:
    label = QLabel(text)
    if role:
        label.setProperty("role", role)
    return label


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, text: str, role: Optional[str] = None, tooltip: str = "") -> None:
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if role:
            self.setProperty("role", role)
        if tooltip:
            self.setToolTip(tooltip)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt override
        point = event.position().toPoint() if hasattr(event, "position") else event.pos()
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(point):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


def make_clickable_label(text: str, role: Optional[str] = None, tooltip: str = "") -> ClickableLabel:
    return ClickableLabel(text, role, tooltip)


def make_button(text: str = "", role: Optional[str] = None, tooltip: str = "") -> QPushButton:
    button = QPushButton(text)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setFocusPolicy(WIDGET_NO_FOCUS)
    if role:
        button.setProperty("role", role)
    if tooltip:
        button.setToolTip(tooltip)
    return button


def addon_logo_icon() -> QIcon:
    return QIcon(str(ADDON_LOGO_PATH))


def set_addon_window_icon(widget: QWidget) -> None:
    widget.setWindowIcon(addon_logo_icon())


def set_accent_property(widget: QWidget, color: str) -> None:
    widget.setStyleSheet(f"color: {color};")


def mode_label_text(state: PomodoroTimerState) -> str:
    text = tr("mode.break_time") if state.mode == MODE_BREAK else tr("mode.pomodoro")
    return text.upper()


def make_toolbar_icon_button(symbol: str, tooltip: str, color: str = COLORS["muted"], font_size: int = 16) -> QPushButton:
    button = make_button(symbol, "toolbarIcon", tooltip)
    button.setFixedSize(34, 34)
    button.setStyleSheet(_icon_button_style(color, font_size))
    return button


def make_stop_button(color: str = COLORS["muted"], font_size: int = 14) -> QPushButton:
    button = make_toolbar_icon_button("", tr("tooltip.stop"), color, font_size)
    button.setIcon(QIcon(str(STOP_ICON_PATH)))
    button.setIconSize(QSize(20, 20))
    return button


def make_sound_button(color: str = COLORS["muted"], font_size: int = 17) -> QPushButton:
    button = make_toolbar_icon_button("", tr("tooltip.sound"), color, font_size)
    button.setIcon(QIcon(str(SOUNDCLOUD_ICON_PATH)))
    button.setIconSize(QSize(21, 21))
    return button


def make_settings_button(color: str = COLORS["muted_light"], font_size: int = 16) -> QPushButton:
    button = make_toolbar_icon_button("", tr("tooltip.settings"), color, font_size)
    button.setIcon(QIcon(str(SETTINGS_ICON_PATH)))
    button.setIconSize(QSize(20, 20))
    return button


def make_pause_button(color: str = COLORS["muted"], font_size: int = 16) -> QPushButton:
    button = make_toolbar_icon_button("", tr("tooltip.pause_resume"), color, font_size)
    button.setIcon(QIcon(str(PLAY_ICON_PATH)))
    button.setIconSize(QSize(18, 18))
    return button


def make_primary_pause_button() -> QPushButton:
    button = make_button("", "primaryPause", tr("tooltip.pause_resume"))
    button.setIcon(QIcon(str(PLAY_ICON_PATH)))
    button.setIconSize(QSize(16, 16))
    button.setFixedSize(50, 36)
    button.setStyleSheet(_primary_pause_style())
    return button


def set_pause_button_state(button: QPushButton, paused: bool, primary: bool = False) -> None:
    icon_path = PLAY_ICON_PATH if paused else PAUSE_ICON_PATH
    icon_size = 16 if primary else (18 if paused else 14)
    button.setText("")
    button.setIcon(QIcon(str(icon_path)))
    button.setIconSize(QSize(icon_size, icon_size))
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
            font-size: 14px;
            font-weight: {weight};
            line-height: 20px;
        }}
        QPushButton:hover {{
            background: {COLORS['soft']};
            border-radius: 999px;
        }}
        """
    )
    return button


class IconTextLabel(QWidget):
    def __init__(
        self,
        icon_path: Path,
        text: str,
        role: Optional[str] = None,
        icon_size: int = 12,
        spacing: int = 4,
        trailing_icon_path: Optional[Path] = None,
        trailing_icon_size: Optional[int] = None,
    ) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)

        icon = QLabel()
        icon.setPixmap(QIcon(str(icon_path)).pixmap(icon_size, icon_size))
        icon.setFixedSize(icon_size, icon_size)

        self._label = QLabel(text)
        if role:
            self._label.setProperty("role", role)

        layout.addWidget(icon)
        layout.addWidget(self._label)
        if trailing_icon_path is not None:
            trailing_icon = QLabel()
            trailing_size = trailing_icon_size or icon_size
            trailing_icon.setPixmap(QIcon(str(trailing_icon_path)).pixmap(trailing_size, trailing_size))
            trailing_icon.setFixedSize(trailing_size, trailing_size)
            layout.addWidget(trailing_icon)
        layout.addStretch(1)

    def setText(self, text: str) -> None:  # noqa: N802 - Qt-compatible API
        self._label.setText(text)

    def text(self) -> str:
        return self._label.text()


def make_icon_text_label(
    icon_path: Path,
    text: str,
    role: Optional[str] = None,
    icon_size: int = 12,
    spacing: int = 4,
    trailing_icon_path: Optional[Path] = None,
    trailing_icon_size: Optional[int] = None,
) -> IconTextLabel:
    return IconTextLabel(icon_path, text, role, icon_size, spacing, trailing_icon_path, trailing_icon_size)


def set_button_icon(button: QPushButton, icon_path: Path, icon_size: int = 14) -> None:
    button.setIcon(QIcon(str(icon_path)))
    button.setIconSize(QSize(icon_size, icon_size))


def make_icon_label(icon_path: Path, icon_size: int = 12) -> QLabel:
    label = QLabel()
    label.setPixmap(QIcon(str(icon_path)).pixmap(icon_size, icon_size))
    label.setFixedSize(icon_size, icon_size)
    return label


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


def make_session_tomato_icons(metrics: SessionMetrics, icon_size: int = 12) -> QIcon:
    total = max(1, int(metrics.session_total))
    done = max(0, min(int(metrics.session_index) - 1, total))
    width = total * icon_size + max(0, total - 1) * 2
    pixmap = QIcon(str(TOMATO_INCOMPLETE_ICON_PATH)).pixmap(QSize(width, icon_size))
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    for index in range(total):
        icon_path = TOMATO_COMPLETED_ICON_PATH if index < done else TOMATO_INCOMPLETE_ICON_PATH
        painter.drawPixmap(index * (icon_size + 2), 0, QIcon(str(icon_path)).pixmap(icon_size, icon_size))
    painter.end()
    return QIcon(pixmap)


def make_session_tomato_html(metrics: SessionMetrics, icon_size: int = 12) -> str:
    total = max(1, int(metrics.session_total))
    done = max(0, min(int(metrics.session_index) - 1, total))
    icons = []
    for index in range(total):
        icon_path = TOMATO_COMPLETED_ICON_PATH if index < done else TOMATO_INCOMPLETE_ICON_PATH
        icons.append(
            f'<img src="{_svg_data_uri(icon_path)}" width="{icon_size}" height="{icon_size}" style="vertical-align:-2px;" />'
        )
    return f"{' '.join(icons)} <span>{metrics.session_index}/{metrics.session_total}</span>"


def make_session_dot_html(metrics: SessionMetrics) -> str:
    total = max(1, int(metrics.session_total))
    done = max(0, min(int(metrics.session_index) - 1, total))
    dots = []
    for index in range(total):
        if index < done:
            dots.append(
                f'<img src="{_svg_data_uri(RED_CIRCLE_ICON_PATH)}" width="8" height="8" style="vertical-align:0px; margin-right:4px;" />'
            )
        else:
            dots.append(
                f'<img src="{_svg_data_uri(BLACK_CIRCLE_ICON_PATH)}" width="8" height="8" style="vertical-align:0px; margin-right:4px;" />'
            )
    return f"{''.join(dots)} <span>{metrics.session_index}/{metrics.session_total}</span>"


def _svg_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def make_sidebar_metric_button(label: str, value: str, tooltip: str = "", color: Optional[str] = None) -> QPushButton:
    button = make_button(f"{label:<14}{value}", "metric", tooltip)
    text_color = color or COLORS["text"]
    button.setStyleSheet(
        f"""
        QPushButton {{
            color: {text_color};
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
    button = make_button(text, "audioMini", tr("tooltip.sound"))
    button.setIcon(QIcon(str(SOUNDCLOUD_ICON_PATH)))
    button.setIconSize(QSize(16, 16))
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
        line-height: 34px;
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
