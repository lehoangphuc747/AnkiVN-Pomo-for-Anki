"""Cards Studied metric value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CardsStudiedMetrics:
    cards: int = 0
    retention: int = 0
    learning_cards: int = 0
    review_cards: int = 0
    relearning_cards: int = 0
    filtered_cards: int = 0
    again_cards: int = 0
    hard_cards: int = 0
    good_cards: int = 0
    easy_cards: int = 0


__all__ = ["CardsStudiedMetrics"]
