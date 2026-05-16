"""QSS and styling helpers for the Pomodoro UI."""

from __future__ import annotations


COLORS = {
    "bg": "#F8F7F3",
    "window": "#FCFBF9",
    "border": "#E8E6E0",
    "text": "#3E3C38",
    "muted": "#8C8A84",
    "muted_light": "#A6A39C",
    "red": "#D94B43",
    "red_dark": "#C23F38",
    "red_light": "#FEF6F5",
    "green": "#739E73",
    "pink": "#F6908F",
    "yellow": "#FBC02D",
    "badge": "#F5EFE6",
    "soft": "#F2F1EC",
}

COLORS_DARK = {
    "bg": "#2A2A2C",
    "window": "#34343A",
    "border": "#4A4A4F",
    "text": "#F2F2F2",
    "muted": "#B5B3AD",
    "muted_light": "#8E8C86",
    "red": "#F28278",
    "red_dark": "#EF5350",
    "red_light": "#5A2E2A",
    "green": "#9CCC9C",
    "pink": "#F8A8A8",
    "yellow": "#FFD54F",
    "badge": "#3A3A3F",
    "soft": "#3F3F44",
}


def _is_system_dark() -> bool:
    """Detect if the OS is using dark mode."""
    try:
        from aqt.qt import QApplication
        app = QApplication.instance()
        if app is not None:
            palette = app.palette()
            bg = palette.color(palette.ColorRole.Window)
            return bg.lightness() < 128
    except Exception:
        pass
    return False


def resolve_colors(theme: str = "system") -> dict:
    """Return the active color palette based on theme setting."""
    if theme == "dark":
        return COLORS_DARK
    if theme == "light":
        return COLORS
    # system
    return COLORS_DARK if _is_system_dark() else COLORS


_ACTIVE_THEME = "system"


def set_active_theme(theme: str) -> None:
    """Track the currently applied theme so palette helpers stay in sync."""
    global _ACTIVE_THEME
    _ACTIVE_THEME = theme if theme in ("system", "light", "dark") else "system"


def active_colors() -> dict:
    """Return the colors palette for the currently applied theme."""
    return resolve_colors(_ACTIVE_THEME)


def is_dark_active() -> bool:
    """Return True when the active theme resolves to the dark palette."""
    return active_colors() is COLORS_DARK


def addon_qss(theme: str = "system") -> str:
    c = resolve_colors(theme)
    set_active_theme(theme)
    return f"""
    QWidget {{
        color: {c["text"]};
        font-family: "Segoe UI", "Arial";
        font-size: 12px;
    }}
    QDialog {{
        background: {c["window"]};
        color: {c["text"]};
    }}
    QFrame[panel="root"] {{
        background: {c["window"]};
        border: 1px solid {c["border"]};
    }}
    QFrame[panel="under"] {{
        background: {c["window"]};
        border: 0;
        border-bottom: 1px solid {c["border"]};
    }}
    QFrame[panel="sidebar"] {{
        background: {c["window"]};
        border: 0;
    }}
    QFrame[panel="corner"] {{
        background: {c["window"]};
        border: 1px solid {c["border"]};
        border-radius: 24px;
    }}
    QLabel[role="mode"] {{
        color: {c["red"]};
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 1px;
    }}
    QLabel[role="brand"] {{
        color: {c["red"]};
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 1px;
    }}
    QLabel[role="timer"] {{
        color: {c["red"]};
        font-size: 31px;
        font-weight: 650;
        min-height: 34px;
        padding: 0;
    }}
    QLabel[role="timerSmall"] {{
        color: {c["text"]};
        font-size: 26px;
        font-weight: 650;
        min-height: 34px;
        padding: 0;
    }}
    QLabel[role="muted"] {{
        color: {c["muted"]};
    }}
    QLabel[role="caption"] {{
        color: {c["muted_light"]};
        font-size: 10px;
        font-weight: 700;
    }}
    QPushButton {{
        background: transparent;
        border: 0;
        color: {c["text"]};
        padding: 4px 6px;
    }}
    QPushButton:hover {{
        background: {c["soft"]};
        border-radius: 9px;
    }}
    QPushButton[role="pill"] {{
        color: {c["muted"]};
        border-radius: 999px;
        padding: 4px 6px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton[role="metric"] {{
        color: {c["text"]};
        border-radius: 12px;
        padding: 4px 6px;
        font-size: 13px;
        text-align: left;
    }}
    QPushButton[role="primary"] {{
        background: {c["red"]};
        color: white;
        border: 1px solid {c["red_dark"]};
        border-radius: 9px;
        padding: 7px 12px;
        font-weight: 600;
    }}
    QPushButton[role="primary"]:hover {{
        background: {c["red_dark"]};
        border-radius: 9px;
    }}
    QPushButton[role="secondary"]:hover {{
        border-radius: 9px;
    }}
    QPushButton[role="metric"]:hover {{
        border-radius: 12px;
    }}
    QPushButton[role="pill"]:hover {{
        border-radius: 999px;
    }}
    QPushButton[role="icon"]:hover {{
        border-radius: 8px;
    }}
    QPushButton[role="secondary"] {{
        background: {c["window"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: 9px;
        padding: 7px 12px;
        font-weight: 600;
    }}
    QPushButton[role="icon"] {{
        color: {c["muted"]};
        border-radius: 8px;
        min-width: 28px;
        min-height: 28px;
        max-width: 28px;
        max-height: 28px;
        padding: 0;
    }}
    QPushButton[active="true"] {{
        background: {c["red_light"]};
        color: {c["red"]};
    }}
    QPushButton[role="primary"][active="true"] {{
        background: {c["red"]};
        color: white;
    }}
    QProgressBar {{
        background: {c["border"]};
        border: 0;
        border-radius: 3px;
        height: 6px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: {c["red"]};
        border-radius: 3px;
    }}
    QComboBox, QSpinBox, QLineEdit {{
        background: {c["window"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 5px 8px;
        min-height: 22px;
    }}
    QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
        border: 1px solid {c["red"]};
    }}
    QDockWidget {{
        titlebar-close-icon: none;
        titlebar-normal-icon: none;
    }}
    """


def refresh_style(widget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()
