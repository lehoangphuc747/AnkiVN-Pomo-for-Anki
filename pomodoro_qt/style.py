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
    "bg": "#1E1E1E",
    "window": "#252525",
    "border": "#3A3A3A",
    "text": "#E0E0E0",
    "muted": "#9E9E9E",
    "muted_light": "#757575",
    "red": "#E57373",
    "red_dark": "#EF5350",
    "red_light": "#3D2222",
    "green": "#81C784",
    "pink": "#F48FB1",
    "yellow": "#FFD54F",
    "badge": "#2C2C2C",
    "soft": "#2E2E2E",
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


def addon_qss(theme: str = "system") -> str:
    c = resolve_colors(theme)
    return f"""
    QWidget {{
        color: {c["text"]};
        font-family: "Segoe UI", "Arial";
        font-size: 12px;
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
