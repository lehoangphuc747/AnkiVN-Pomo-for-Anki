"""Experience and level metric value object."""

from __future__ import annotations

from dataclasses import dataclass


XP_PER_UNIQUE_CARD = 1
XP_PER_ANKI_REVIEW_EVENT = 0

LEVEL_THRESHOLDS = {
    1: 0,
    2: 20,
    3: 50,
    4: 90,
    5: 140,
    6: 200,
    7: 270,
    8: 350,
    9: 440,
    10: 550,
}


@dataclass
class ExperienceMetrics:
    level: int = 1
    experience: int = 0
    level_floor_experience: int = 0
    next_level_experience: int = 20
    experience_to_next_level: int = 20
    level_progress: int = 0
    streak_days: int = 0
    unique_cards: int = 0
    again_cards: int = 0
    hard_cards: int = 0
    good_cards: int = 0
    easy_cards: int = 0


def answer_experience(ease: int | None = None) -> int:
    return XP_PER_ANKI_REVIEW_EVENT


def unique_cards_experience(unique_cards: int = 0) -> int:
    try:
        cards = int(unique_cards)
    except (TypeError, ValueError):
        cards = 0
    return max(0, cards) * XP_PER_UNIQUE_CARD


def level_state(experience: int) -> dict[str, int]:
    experience = max(0, int(experience))
    level = 1
    while _level_threshold(level + 1) <= experience:
        level += 1

    floor_experience = _level_threshold(level)
    next_level_experience = _level_threshold(level + 1)
    span = max(1, next_level_experience - floor_experience)
    earned_in_level = max(0, experience - floor_experience)
    return {
        "level": level,
        "floor_experience": floor_experience,
        "floor_xp": floor_experience,
        "next_level_experience": next_level_experience,
        "next_level_xp": next_level_experience,
        "experience_to_next_level": max(0, next_level_experience - experience),
        "xp_to_next_level": max(0, next_level_experience - experience),
        "progress": round(earned_in_level * 100 / span),
    }


def _level_threshold(level: int) -> int:
    if level <= 1:
        return 0
    if level in LEVEL_THRESHOLDS:
        return LEVEL_THRESHOLDS[level]

    threshold = LEVEL_THRESHOLDS[10]
    for next_level in range(11, level + 1):
        threshold += 120 + (next_level - 10) * 20
    return threshold


__all__ = [
    "ExperienceMetrics",
    "XP_PER_UNIQUE_CARD",
    "XP_PER_ANKI_REVIEW_EVENT",
    "answer_experience",
    "unique_cards_experience",
    "level_state",
]
