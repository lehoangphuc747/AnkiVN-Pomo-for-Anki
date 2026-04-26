"""Pomodoro session history popover."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from .i18n import tr
from .metric_popover import MetricPopover
from .models import MODE_BREAK, SessionHistoryEntry, SessionMetrics
from .style import COLORS


class SessionHistoryPopover(MetricPopover):
    def __init__(self, metrics: SessionMetrics, history: Sequence[SessionHistoryEntry] = ()) -> None:
        super().__init__(320)
        self.add_header(
            "P",
            tr("metric.session_history"),
            tr("session.pomodoro_count", index=metrics.session_index, total=metrics.session_total),
            tr("session.subtitle_today"),
        )

        for entry in list(history)[-4:]:
            self.add_timeline_item(
                _marker(entry),
                _title(entry),
                _time_text(entry.ended_at),
                _detail(entry),
                COLORS["green"] if entry.mode == MODE_BREAK else COLORS["red"],
            )

        self.add_timeline_item(
            str(metrics.session_index),
            tr("session.pomodoro_count", index=metrics.session_index, total=metrics.session_total),
            tr("state.now"),
            tr("session.current_detail", cards=metrics.cards, retention=metrics.retention, xp=metrics.session_xp),
            COLORS["red"],
            is_last=True,
        )


def make_session_history_popover(
    metrics: SessionMetrics,
    history: Sequence[SessionHistoryEntry] = (),
) -> SessionHistoryPopover:
    return SessionHistoryPopover(metrics, history)


def _marker(entry: SessionHistoryEntry) -> str:
    if entry.mode == MODE_BREAK:
        return "B"
    return str(entry.session_index)


def _title(entry: SessionHistoryEntry) -> str:
    if entry.mode == MODE_BREAK:
        return tr("session.break")
    return tr("session.pomodoro_count", index=entry.session_index, total=entry.session_total)


def _detail(entry: SessionHistoryEntry) -> str:
    status = tr("state.completed") if entry.completed else tr("state.stopped")
    minutes = max(0, round(entry.duration_seconds / 60))
    if entry.mode == MODE_BREAK:
        return tr("session.history_break_detail", status=status, minutes=minutes)
    deck = tr("session.deck_suffix", deck=entry.deck_name) if entry.deck_name else ""
    return tr(
        "session.history_focus_detail",
        status=status,
        minutes=minutes,
        cards=entry.cards,
        retention=entry.retention,
        xp=entry.xp,
        deck=deck,
    )


def _time_text(value: str) -> str:
    if not value:
        return "--:--"
    try:
        return datetime.fromisoformat(value).strftime("%H:%M")
    except ValueError:
        return "--:--"


__all__ = ["SessionHistoryPopover", "make_session_history_popover"]
