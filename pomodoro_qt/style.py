"""QSS and styling helpers for the Pomodoro UI."""

from __future__ import annotations

from typing import Optional, Tuple


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


DEFAULT_ACCENT_LIGHT = COLORS["red"]
DEFAULT_ACCENT_DARK = COLORS_DARK["red"]


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


def _normalize_hex(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if not text.startswith("#"):
        text = "#" + text
    if len(text) == 4:
        text = "#" + "".join(ch * 2 for ch in text[1:])
    if len(text) != 7:
        return None
    try:
        int(text[1:], 16)
    except ValueError:
        return None
    return text.upper()


def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02X}{g:02X}{b:02X}"


def _shade(hex_color: str, factor: float) -> str:
    """Return a shaded version of ``hex_color``.

    factor < 0 → darker, factor > 0 → lighter, both in range -1..1.
    """
    r, g, b = _hex_to_rgb(hex_color)
    if factor < 0:
        # Darken: blend toward black.
        amount = min(1.0, -factor)
        r = r * (1 - amount)
        g = g * (1 - amount)
        b = b * (1 - amount)
    else:
        amount = min(1.0, factor)
        r = r + (255 - r) * amount
        g = g + (255 - g) * amount
        b = b + (255 - b) * amount
    return _rgb_to_hex(r, g, b)


def _derive_accent(accent_hex: str, *, dark: bool) -> Tuple[str, str, str]:
    """Return (accent, accent_dark, accent_light) given a base accent color."""
    base = accent_hex
    if dark:
        # Dark theme: darker tinted background, lighter highlight.
        return base, _shade(base, -0.18), _shade(base, -0.55)
    return base, _shade(base, -0.12), _shade(base, 0.86)


def _apply_accent(palette: dict, accent_hex: Optional[str], *, dark: bool) -> dict:
    if not accent_hex:
        return palette
    normalized = _normalize_hex(accent_hex)
    if not normalized:
        return palette
    red, red_dark, red_light = _derive_accent(normalized, dark=dark)
    result = dict(palette)
    result["red"] = red
    result["red_dark"] = red_dark
    result["red_light"] = red_light
    return result


def resolve_colors(theme: str = "system", accent_color: Optional[str] = None) -> dict:
    """Return the active color palette based on theme + optional accent override."""
    if theme == "dark":
        return _apply_accent(COLORS_DARK, accent_color, dark=True)
    if theme == "light":
        return _apply_accent(COLORS, accent_color, dark=False)
    # system
    if _is_system_dark():
        return _apply_accent(COLORS_DARK, accent_color, dark=True)
    return _apply_accent(COLORS, accent_color, dark=False)


_ACTIVE_THEME = "system"
_ACTIVE_ACCENT: Optional[str] = None


def set_active_theme(theme: str, accent_color: Optional[str] = None) -> None:
    """Track the currently applied theme so palette helpers stay in sync."""
    global _ACTIVE_THEME, _ACTIVE_ACCENT
    _ACTIVE_THEME = theme if theme in ("system", "light", "dark") else "system"
    _ACTIVE_ACCENT = _normalize_hex(accent_color)


def active_colors() -> dict:
    """Return the colors palette for the currently applied theme + accent."""
    return resolve_colors(_ACTIVE_THEME, _ACTIVE_ACCENT)


def is_dark_active() -> bool:
    """Return True when the active theme resolves to the dark palette."""
    if _ACTIVE_THEME == "dark":
        return True
    if _ACTIVE_THEME == "light":
        return False
    return _is_system_dark()


def addon_qss(theme: str = "system", accent_color: Optional[str] = None) -> str:
    c = resolve_colors(theme, accent_color)
    set_active_theme(theme, accent_color)
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
