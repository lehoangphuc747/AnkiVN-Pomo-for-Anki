"""Study-time metric value object and formatting helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .i18n import current_language


@dataclass(frozen=True)
class StudyTimeMetrics:
    today_seconds: int = 0
    all_time_seconds: int = 0
    today_reviews: int = 0
    all_time_reviews: int = 0
    cutoff_seconds: int = 4 * 3600
    seconds_until_cutoff: int = 0


def format_study_duration(seconds: int) -> str:
    total_minutes = max(0, round(max(0, int(seconds)) / 60))
    hours, minutes = divmod(total_minutes, 60)
    if hours <= 0:
        return f"{minutes}m"
    return f"{hours}h {minutes:02d}m"


def format_study_duration_long(seconds: int) -> str:
    total_minutes = max(0, round(max(0, int(seconds)) / 60))
    hours, minutes = divmod(total_minutes, 60)
    if current_language() == "vi":
        return f"{hours} gi\u1edd {minutes:02d} ph\u00fat"
    return f"{hours}h {minutes:02d}m"


def format_cutoff_time(seconds: int) -> str:
    total_minutes = max(0, int(seconds) // 60)
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}:{minutes:02d}"


__all__ = [
    "StudyTimeMetrics",
    "format_cutoff_time",
    "format_study_duration",
    "format_study_duration_long",
]
