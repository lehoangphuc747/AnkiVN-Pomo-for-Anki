"""Anki reviewer hook adapter for real study metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


CARD_KIND_NEW = "new"
CARD_KIND_REVIEW = "review"


try:
    from anki.consts import (
        CARD_TYPE_NEW,
        QUEUE_TYPE_NEW,
    )
except Exception:
    CARD_TYPE_NEW = 0
    QUEUE_TYPE_NEW = 0


@dataclass(frozen=True)
class ReviewAnswerEvent:
    card_id: int
    ease: int
    card_kind: str
    deck_id: Optional[int] = None
    deck_name: str = ""


@dataclass(frozen=True)
class CardAnswerSnapshot:
    card_id: int
    card_kind: str
    deck_id: Optional[int]
    deck_name: str


class ReviewTracker:
    """Converts Anki reviewer hooks into stable answer events."""

    def __init__(
        self,
        on_answer: Callable[[ReviewAnswerEvent], None],
        deck_name_for_id: Callable[[Optional[int]], str],
    ) -> None:
        self._on_answer = on_answer
        self._deck_name_for_id = deck_name_for_id
        self._pending: dict[tuple[int, int], CardAnswerSnapshot] = {}

    def on_pre_answer(self, ease_tuple, reviewer, card):
        try:
            card_id = _card_id(card)
            key = (id(reviewer), card_id)
            deck_id = _deck_id(card)
            self._pending[key] = CardAnswerSnapshot(
                card_id=card_id,
                card_kind=_classify_card(card),
                deck_id=deck_id,
                deck_name=self._deck_name_for_id(deck_id),
            )
        except Exception:
            pass
        return ease_tuple

    def on_did_answer(self, reviewer, card, ease) -> None:
        try:
            card_id = _card_id(card)
            snapshot = self._pending.pop((id(reviewer), card_id), None)
            if snapshot is None:
                deck_id = _deck_id(card)
                snapshot = CardAnswerSnapshot(
                    card_id=card_id,
                    card_kind=_classify_card(card),
                    deck_id=deck_id,
                    deck_name=self._deck_name_for_id(deck_id),
                )
            self._on_answer(
                ReviewAnswerEvent(
                    card_id=snapshot.card_id,
                    ease=int(ease),
                    card_kind=snapshot.card_kind,
                    deck_id=snapshot.deck_id,
                    deck_name=snapshot.deck_name,
                )
            )
        except Exception:
            pass

    def on_reviewer_end(self, *args) -> None:
        self._pending.clear()


def _classify_card(card) -> str:
    card_type = getattr(card, "type", None)
    queue = getattr(card, "queue", None)
    if card_type == CARD_TYPE_NEW or queue == QUEUE_TYPE_NEW:
        return CARD_KIND_NEW
    return CARD_KIND_REVIEW


def _card_id(card) -> int:
    return int(getattr(card, "id", 0) or 0)


def _deck_id(card) -> Optional[int]:
    try:
        return int(card.current_deck_id())
    except Exception:
        try:
            return int(getattr(card, "did", 0) or 0)
        except Exception:
            return None
