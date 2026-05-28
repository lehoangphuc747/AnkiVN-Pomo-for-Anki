"""Pure helpers for local audio volume state."""

from __future__ import annotations


DEFAULT_LOCAL_VOLUME_PERCENT = 65
LOCAL_VOLUME_STATE_KEY = "local_volume_percent"


def clamp_local_volume_percent(value: object, fallback: int = DEFAULT_LOCAL_VOLUME_PERCENT) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = int(fallback)
    return max(0, min(100, parsed))


def local_volume_fraction(value: object) -> float:
    return clamp_local_volume_percent(value) / 100.0


def local_volume_label(value: object) -> str:
    return f"{clamp_local_volume_percent(value)}%"


__all__ = [
    "DEFAULT_LOCAL_VOLUME_PERCENT",
    "LOCAL_VOLUME_STATE_KEY",
    "clamp_local_volume_percent",
    "local_volume_fraction",
    "local_volume_label",
]
