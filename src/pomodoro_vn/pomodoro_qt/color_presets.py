"""Color preset definitions for the Pomodoro UI.

Each preset defines an accent color (used during Pomodoro mode) and a break
color (used during break mode). The ``id`` is persisted in config; the
``label_key`` is an i18n key rendered in the Settings dropdown.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ColorPreset:
    id: str
    label_key: str
    accent: str  # Pomodoro accent
    break_color: str  # Break accent
    bg_tint: str = ""  # Background tint (empty = no tint)


PRESETS: tuple[ColorPreset, ...] = (
    ColorPreset("classic", "preset.classic", "#D94B43", "#739E73", ""),
    ColorPreset("ocean", "preset.ocean", "#2196F3", "#26A69A", "#E3F2FD"),
    ColorPreset("sakura", "preset.sakura", "#E91E63", "#AB47BC", "#FCE4EC"),
    ColorPreset("midnight", "preset.midnight", "#7C4DFF", "#448AFF", "#EDE7F6"),
    ColorPreset("sunset", "preset.sunset", "#FF6D00", "#FFB300", "#FFF3E0"),
    ColorPreset("forest", "preset.forest", "#2E7D32", "#558B2F", "#E8F5E9"),
    ColorPreset("mocha", "preset.mocha", "#795548", "#8D6E63", "#EFEBE9"),
)

CUSTOM_PRESET_ID = "custom"
DEFAULT_PRESET_ID = "classic"

_PRESET_MAP = {p.id: p for p in PRESETS}


def get_preset(preset_id: str) -> Optional[ColorPreset]:
    """Return the preset for the given id, or None if not found."""
    return _PRESET_MAP.get(preset_id)


def preset_ids() -> list[str]:
    return [p.id for p in PRESETS]


def default_preset() -> ColorPreset:
    return _PRESET_MAP[DEFAULT_PRESET_ID]
