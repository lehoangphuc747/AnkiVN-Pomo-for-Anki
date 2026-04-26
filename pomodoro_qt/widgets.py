"""Compatibility exports for Pomodoro Qt widgets.

New code should import from focused modules such as ``ui_components``,
``under_toolbar``, ``sidebar_panel``, ``corner_badge``, ``settings_dialog``,
and ``dialogs``.
"""

from __future__ import annotations

from .corner_badge import HtmlCornerBadgeWidget
from .dialogs import PomodoroDoneDialog
from .settings_dialog import SettingsDialog
from .sidebar_panel import SidebarWidget
from .ui_components import (
    ALIGN_CENTER,
    SYMBOL_BREAK,
    SYMBOL_CLOSE,
    SYMBOL_FIRE,
    SYMBOL_GEAR,
    SYMBOL_LIGHTNING,
    SYMBOL_MUSIC,
    SYMBOL_PAUSE,
    SYMBOL_PLAY,
    SYMBOL_REPEAT,
    SYMBOL_SKIP_BACK,
    SYMBOL_SKIP_FORWARD,
    SYMBOL_SPARKLE,
    SYMBOL_STOP,
    SYMBOL_TOMATO,
    CircularProgress,
    make_button,
    make_label,
    make_toolbar_icon_button,
    make_pill_button,
    mode_label_text,
    set_accent_property,
    set_pause_button_state as set_timer_control_icon,
    set_toolbar_metric_style as style_toolbar_metric_button,
)
from .under_toolbar import UnderToolbarWidget


CornerBadgeWidget = HtmlCornerBadgeWidget


def make_icon_button(symbol: str, tooltip: str, color: str = "#8C8A84", font_size: int = 16):
    return make_toolbar_icon_button(symbol, tooltip, color, font_size)


__all__ = [
    "ALIGN_CENTER",
    "SYMBOL_BREAK",
    "SYMBOL_CLOSE",
    "SYMBOL_FIRE",
    "SYMBOL_GEAR",
    "SYMBOL_LIGHTNING",
    "SYMBOL_MUSIC",
    "SYMBOL_PAUSE",
    "SYMBOL_PLAY",
    "SYMBOL_REPEAT",
    "SYMBOL_SKIP_BACK",
    "SYMBOL_SKIP_FORWARD",
    "SYMBOL_SPARKLE",
    "SYMBOL_STOP",
    "SYMBOL_TOMATO",
    "CircularProgress",
    "CornerBadgeWidget",
    "HtmlCornerBadgeWidget",
    "PomodoroDoneDialog",
    "SettingsDialog",
    "SidebarWidget",
    "UnderToolbarWidget",
    "make_button",
    "make_icon_button",
    "make_label",
    "make_pill_button",
    "mode_label_text",
    "set_accent_property",
    "set_timer_control_icon",
    "style_toolbar_metric_button",
]
