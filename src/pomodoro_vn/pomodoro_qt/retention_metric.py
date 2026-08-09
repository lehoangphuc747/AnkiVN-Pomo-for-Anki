"""Retention metric value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetentionMetrics:
    today_retention: int = 0
    today_cards: int = 0
    again_cards: int = 0
    hard_cards: int = 0
    good_cards: int = 0
    easy_cards: int = 0
    all_time_retention: int = 0
    all_time_cards: int = 0


__all__ = ["RetentionMetrics"]
