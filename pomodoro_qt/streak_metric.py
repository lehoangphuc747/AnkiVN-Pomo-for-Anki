"""Study streak metric value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StreakMetrics:
    days: int = 0
    longest_days: int = 0
    start_date: str = ""
    today_reviews: int = 0
    yesterday_reviews: int = 0
    cutoff_hour: int = 4
    seconds_until_cutoff: int = 0


__all__ = ["StreakMetrics"]
