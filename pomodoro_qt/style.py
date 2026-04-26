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
    "badge": "#F5EFE6",
    "soft": "#F2F1EC",
}


def addon_qss() -> str:
    return f"""
    QWidget {{
        color: {COLORS["text"]};
        font-family: "Segoe UI", "Arial";
        font-size: 12px;
    }}
    QFrame[panel="root"] {{
        background: {COLORS["window"]};
        border: 1px solid {COLORS["border"]};
    }}
    QFrame[panel="under"] {{
        background: {COLORS["window"]};
        border: 0;
        border-bottom: 1px solid {COLORS["border"]};
    }}
    QFrame[panel="sidebar"] {{
        background: #FCFBF8;
        border: 0;
        border-right: 1px solid #E0DED5;
    }}
    QFrame[panel="corner"] {{
        background: {COLORS["window"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 24px;
    }}
    QLabel[role="mode"] {{
        color: {COLORS["red"]};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    QLabel[role="timer"] {{
        color: {COLORS["red"]};
        font-size: 28px;
        font-weight: 650;
        min-height: 32px;
        padding: 0;
    }}
    QLabel[role="timerSmall"] {{
        color: {COLORS["text"]};
        font-size: 26px;
        font-weight: 650;
        min-height: 34px;
        padding: 0;
    }}
    QLabel[role="muted"] {{
        color: {COLORS["muted"]};
    }}
    QLabel[role="caption"] {{
        color: {COLORS["muted_light"]};
        font-size: 10px;
        font-weight: 700;
    }}
    QPushButton {{
        background: transparent;
        border: 0;
        color: {COLORS["text"]};
        padding: 4px 6px;
    }}
    QPushButton:hover {{
        background: {COLORS["soft"]};
        border-radius: 9px;
    }}
    QPushButton[role="pill"] {{
        color: {COLORS["muted"]};
        border-radius: 999px;
        padding: 4px 6px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton[role="metric"] {{
        color: {COLORS["text"]};
        border-radius: 12px;
        padding: 4px 6px;
        font-size: 13px;
        text-align: left;
    }}
    QPushButton[role="primary"] {{
        background: {COLORS["red"]};
        color: white;
        border: 1px solid #BE4239;
        border-radius: 9px;
        padding: 7px 12px;
        font-weight: 600;
    }}
    QPushButton[role="primary"]:hover {{
        background: {COLORS["red_dark"]};
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
        background: #FDFBF9;
        color: #595752;
        border: 1px solid #DEDCD3;
        border-radius: 9px;
        padding: 7px 12px;
        font-weight: 600;
    }}
    QPushButton[role="icon"] {{
        color: {COLORS["muted"]};
        border-radius: 8px;
        min-width: 28px;
        min-height: 28px;
        max-width: 28px;
        max-height: 28px;
        padding: 0;
    }}
    QPushButton[active="true"] {{
        background: {COLORS["red_light"]};
        color: {COLORS["red"]};
    }}
    QPushButton[role="primary"][active="true"] {{
        background: {COLORS["red"]};
        color: white;
    }}
    QProgressBar {{
        background: {COLORS["border"]};
        border: 0;
        border-radius: 3px;
        height: 6px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: {COLORS["red"]};
        border-radius: 3px;
    }}
    QComboBox, QSpinBox, QLineEdit {{
        background: white;
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 5px 8px;
        min-height: 22px;
    }}
    QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
        border: 1px solid {COLORS["red"]};
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
