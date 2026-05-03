"""Shared revlog-backed source for study metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .anki_day import anki_rollover_seconds, anki_today_start, day_key, seconds_until_cutoff
from .cards_metric import CardsStudiedMetrics
from .experience_metric import ExperienceMetrics, level_state, studied_cards_experience
from .retention_metric import RetentionMetrics
from .streak_metric import StreakMetrics


@dataclass(frozen=True)
class EaseCounts:
    cards: int = 0
    again_cards: int = 0
    hard_cards: int = 0
    good_cards: int = 0
    easy_cards: int = 0


@dataclass(frozen=True)
class TodayRevlogCounts:
    cards: int = 0
    learning_cards: int = 0
    review_cards: int = 0
    relearning_cards: int = 0
    filtered_cards: int = 0
    again_cards: int = 0
    hard_cards: int = 0
    good_cards: int = 0
    easy_cards: int = 0

    def ease_counts(self) -> EaseCounts:
        return EaseCounts(
            cards=self.cards,
            again_cards=self.again_cards,
            hard_cards=self.hard_cards,
            good_cards=self.good_cards,
            easy_cards=self.easy_cards,
        )


@dataclass(frozen=True)
class RevlogMetricsSnapshot:
    cards: CardsStudiedMetrics
    experience: ExperienceMetrics
    retention: RetentionMetrics
    streak: StreakMetrics


class RevlogMetricsSource:
    """Computes all user-facing revlog metrics through one cached source."""

    def __init__(self, mw: Any) -> None:
        self._mw = mw
        self._snapshot: RevlogMetricsSnapshot | None = None
        self._snapshot_today: int | None = None
        self._day_rollup: dict[int, int] | None = None
        self._day_rollup_today: int | None = None
        self._all_time_counts: EaseCounts | None = None
        self.last_debug: dict[str, Any] = {}
        self.last_error: Exception | None = None

    def metrics(self) -> RevlogMetricsSnapshot:
        try:
            col = getattr(self._mw, "col", None)
            db = getattr(col, "db", None)
            if db is None:
                return _empty_snapshot()
            rollover_seconds = anki_rollover_seconds(col)
            anki_today = anki_today_start(db, rollover_seconds)
            if self._snapshot is not None and self._snapshot_today == anki_today:
                return self._cached_snapshot(anki_today, rollover_seconds)

            start_ms = _day_start_ms(anki_today, rollover_seconds)
            end_ms = start_ms + 86400 * 1000
            reviews_by_day = self._reviews_by_day(db, anki_today, rollover_seconds)
            today = _today_counts(db, start_ms, end_ms)
            all_time = self._all_time(db)
            streak = _streak_metrics(reviews_by_day, anki_today, rollover_seconds)
            experience = _experience_metrics(db, streak, anki_today, rollover_seconds, today)
            cards = _cards_metrics(today)
            retention = _retention_metrics(today.ease_counts(), all_time)
            snapshot = RevlogMetricsSnapshot(
                cards=cards,
                experience=experience,
                retention=retention,
                streak=streak,
            )
            self._snapshot = snapshot
            self._snapshot_today = anki_today
            self.last_debug = _debug_payload(snapshot, anki_today, rollover_seconds, start_ms, end_ms)
            self.last_error = None
            return snapshot
        except Exception as exc:
            self.last_debug = {"error": f"{type(exc).__name__}: {exc}"}
            self.last_error = exc
            return _empty_snapshot()

    def note_review_answered(self, ease: int | None = None) -> None:
        try:
            col = getattr(self._mw, "col", None)
            db = getattr(col, "db", None)
            if db is None:
                self._clear_snapshot()
                return
            rollover_seconds = anki_rollover_seconds(col)
            anki_today = anki_today_start(db, rollover_seconds)
            normalized_ease = _ease(ease)
            if self._snapshot_today != anki_today:
                self._clear_snapshot()
                self._clear_day_rollup()
                self._increment_cached_all_time(normalized_ease)
                return
            self._increment_cached_day(anki_today)
            self._increment_cached_all_time(normalized_ease)
            self._snapshot = None
        except Exception:
            self._clear_snapshot()

    def _cached_snapshot(self, anki_today: int, rollover_seconds: int) -> RevlogMetricsSnapshot:
        assert self._snapshot is not None
        self.last_debug = {
            **_debug_payload(
                self._snapshot,
                anki_today,
                rollover_seconds,
                _day_start_ms(anki_today, rollover_seconds),
                _day_start_ms(anki_today, rollover_seconds) + 86400 * 1000,
            ),
            "cached": True,
        }
        self.last_error = None
        return self._snapshot

    def _reviews_by_day(self, db: Any, anki_today: int, rollover_seconds: int) -> dict[int, int]:
        if self._day_rollup is not None and self._day_rollup_today == anki_today:
            return self._day_rollup
        rows = db.all(
            """
            SELECT
                CAST(STRFTIME('%s', id / 1000 - ?, 'unixepoch', 'localtime', 'start of day') AS int) AS day,
                COUNT(*) AS reviews
            FROM revlog
            WHERE ease >= 1
            GROUP BY day
            ORDER BY 1
            """,
            rollover_seconds,
        )
        self._day_rollup = {_int(day): _int(reviews) for day, reviews in rows if day is not None}
        self._day_rollup_today = anki_today
        return self._day_rollup

    def _all_time(self, db: Any) -> EaseCounts:
        if self._all_time_counts is not None:
            return self._all_time_counts
        self._all_time_counts = _ease_counts(
            db.first(
                """
                SELECT
                    COUNT(*) AS cards,
                    SUM(CASE WHEN ease = 1 THEN 1 ELSE 0 END) AS again_cards,
                    SUM(CASE WHEN ease = 2 THEN 1 ELSE 0 END) AS hard_cards,
                    SUM(CASE WHEN ease = 3 THEN 1 ELSE 0 END) AS good_cards,
                    SUM(CASE WHEN ease = 4 THEN 1 ELSE 0 END) AS easy_cards
                FROM revlog
                WHERE ease BETWEEN 1 AND 4
                """
            )
        )
        return self._all_time_counts

    def _increment_cached_day(self, anki_today: int) -> None:
        if self._day_rollup is None or self._day_rollup_today != anki_today:
            return
        self._day_rollup[anki_today] = max(0, self._day_rollup.get(anki_today, 0)) + 1

    def _increment_cached_all_time(self, ease: int) -> None:
        if self._all_time_counts is None:
            return
        self._all_time_counts = _increment_ease_counts(self._all_time_counts, ease)

    def _clear_snapshot(self) -> None:
        self._snapshot = None
        self._snapshot_today = None

    def _clear_day_rollup(self) -> None:
        self._day_rollup = None
        self._day_rollup_today = None


def _today_counts(db: Any, start_ms: int, end_ms: int) -> TodayRevlogCounts:
    values = list(
        db.first(
            """
            SELECT
                COUNT(*) AS cards,
                SUM(CASE WHEN type = 0 THEN 1 ELSE 0 END) AS learning_cards,
                SUM(CASE WHEN type = 1 THEN 1 ELSE 0 END) AS review_cards,
                SUM(CASE WHEN type = 2 THEN 1 ELSE 0 END) AS relearning_cards,
                SUM(CASE WHEN type = 3 THEN 1 ELSE 0 END) AS filtered_cards,
                SUM(CASE WHEN ease = 1 THEN 1 ELSE 0 END) AS again_cards,
                SUM(CASE WHEN ease = 2 THEN 1 ELSE 0 END) AS hard_cards,
                SUM(CASE WHEN ease = 3 THEN 1 ELSE 0 END) AS good_cards,
                SUM(CASE WHEN ease = 4 THEN 1 ELSE 0 END) AS easy_cards
            FROM revlog
            WHERE id >= ? AND id < ? AND ease BETWEEN 1 AND 4
            """,
            start_ms,
            end_ms,
        )
        or []
    )
    return TodayRevlogCounts(
        cards=_int_at(values, 0),
        learning_cards=_int_at(values, 1),
        review_cards=_int_at(values, 2),
        relearning_cards=_int_at(values, 3),
        filtered_cards=_int_at(values, 4),
        again_cards=_int_at(values, 5),
        hard_cards=_int_at(values, 6),
        good_cards=_int_at(values, 7),
        easy_cards=_int_at(values, 8),
    )


def _cards_metrics(today: TodayRevlogCounts) -> CardsStudiedMetrics:
    retention = _retention(today.ease_counts())
    return CardsStudiedMetrics(
        cards=today.cards,
        retention=retention,
        learning_cards=today.learning_cards,
        review_cards=today.review_cards,
        relearning_cards=today.relearning_cards,
        filtered_cards=today.filtered_cards,
        again_cards=today.again_cards,
        hard_cards=today.hard_cards,
        good_cards=today.good_cards,
        easy_cards=today.easy_cards,
    )


def _retention_metrics(today: EaseCounts, all_time: EaseCounts) -> RetentionMetrics:
    return RetentionMetrics(
        today_retention=_retention(today),
        today_cards=today.cards,
        again_cards=today.again_cards,
        hard_cards=today.hard_cards,
        good_cards=today.good_cards,
        easy_cards=today.easy_cards,
        all_time_retention=_retention(all_time),
        all_time_cards=all_time.cards,
    )


def _streak_metrics(reviews_by_day: dict[int, int], anki_today: int, rollover_seconds: int) -> StreakMetrics:
    active_days = sorted(day for day, reviews in reviews_by_day.items() if reviews > 0)
    end_day = _current_streak_end_day(active_days, anki_today)
    days = _current_streak_days(active_days, anki_today)
    start_day = _streak_start_day(end_day, days)
    return StreakMetrics(
        days=days,
        longest_days=_longest_streak_days(active_days),
        start_date=day_key(start_day) if start_day is not None else "",
        today_reviews=max(0, reviews_by_day.get(anki_today, 0)),
        yesterday_reviews=max(0, reviews_by_day.get(anki_today - 86400, 0)),
        cutoff_hour=max(0, min(23, int(rollover_seconds) // 3600)),
        seconds_until_cutoff=seconds_until_cutoff(anki_today, rollover_seconds),
    )


def _experience_metrics(
    db: Any,
    streak: StreakMetrics,
    anki_today: int,
    rollover_seconds: int,
    today: TodayRevlogCounts,
) -> ExperienceMetrics:
    if streak.days <= 0:
        return ExperienceMetrics()
    streak_start = _parse_day_key(streak.start_date)
    if streak_start is None:
        return ExperienceMetrics()
    if streak.days == 1 and streak_start == anki_today:
        counts = today.ease_counts()
    else:
        counts = _ease_counts(
            db.first(
                """
                SELECT
                    COUNT(*) AS cards,
                    SUM(CASE WHEN ease = 1 THEN 1 ELSE 0 END) AS again_cards,
                    SUM(CASE WHEN ease = 2 THEN 1 ELSE 0 END) AS hard_cards,
                    SUM(CASE WHEN ease = 3 THEN 1 ELSE 0 END) AS good_cards,
                    SUM(CASE WHEN ease = 4 THEN 1 ELSE 0 END) AS easy_cards
                FROM revlog
                WHERE id >= ? AND id < ? AND ease BETWEEN 1 AND 4
                """,
                _day_start_ms(streak_start, rollover_seconds),
                _day_start_ms(anki_today + 86400, rollover_seconds),
            )
        )
    experience = studied_cards_experience(
        hard_cards=counts.hard_cards,
        good_cards=counts.good_cards,
        easy_cards=counts.easy_cards,
    )
    level = level_state(experience)
    return ExperienceMetrics(
        level=level["level"],
        experience=experience,
        level_floor_experience=level["floor_experience"],
        next_level_experience=level["next_level_experience"],
        experience_to_next_level=level["experience_to_next_level"],
        level_progress=level["progress"],
        streak_days=streak.days,
        again_cards=counts.again_cards,
        hard_cards=counts.hard_cards,
        good_cards=counts.good_cards,
        easy_cards=counts.easy_cards,
    )


def _ease_counts(row: object) -> EaseCounts:
    values = list(row) if row is not None else []
    return EaseCounts(
        cards=_int_at(values, 0),
        again_cards=_int_at(values, 1),
        hard_cards=_int_at(values, 2),
        good_cards=_int_at(values, 3),
        easy_cards=_int_at(values, 4),
    )


def _increment_ease_counts(counts: EaseCounts, ease: int) -> EaseCounts:
    return EaseCounts(
        cards=counts.cards + 1,
        again_cards=counts.again_cards + (1 if ease == 1 else 0),
        hard_cards=counts.hard_cards + (1 if ease == 2 else 0),
        good_cards=counts.good_cards + (1 if ease == 3 else 0),
        easy_cards=counts.easy_cards + (1 if ease == 4 else 0),
    )


def _retention(counts: EaseCounts) -> int:
    if counts.cards <= 0:
        return 0
    correct = counts.hard_cards + counts.good_cards + counts.easy_cards
    return round(correct * 100 / counts.cards)


def _current_streak_end_day(active_days: list[int], today_start: int) -> Optional[int]:
    active = set(active_days)
    if today_start in active:
        return today_start
    yesterday = today_start - 86400
    if yesterday in active:
        return yesterday
    return None


def _current_streak_days(active_days: list[int], today_start: int) -> int:
    end_day = _current_streak_end_day(active_days, today_start)
    if end_day is None:
        return 0
    active = set(active_days)
    streak = 0
    cursor = end_day
    while cursor in active:
        streak += 1
        cursor -= 86400
    return streak


def _streak_start_day(streak_end_day: Optional[int], streak_days: int) -> Optional[int]:
    if streak_end_day is None or streak_days <= 0:
        return None
    return streak_end_day - (streak_days - 1) * 86400


def _longest_streak_days(active_days: list[int]) -> int:
    longest = 0
    current = 0
    previous = None
    for day in active_days:
        if previous is None or day == previous + 86400:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
        previous = day
    return longest


def _parse_day_key(value: str) -> Optional[int]:
    if not value:
        return None
    try:
        from datetime import datetime

        return int(datetime.strptime(value, "%Y-%m-%d").timestamp())
    except Exception:
        return None


def _debug_payload(
    snapshot: RevlogMetricsSnapshot,
    anki_today: int,
    rollover_seconds: int,
    start_ms: int,
    end_ms: int,
) -> dict[str, Any]:
    return {
        "today": anki_today,
        "today_key": day_key(anki_today),
        "rollover_hours": rollover_seconds / 3600,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "cards": snapshot.cards.cards,
        "retention": snapshot.retention.today_retention,
        "all_time_retention": snapshot.retention.all_time_retention,
        "experience": snapshot.experience.experience,
        "level": snapshot.experience.level,
        "streak_days": snapshot.streak.days,
    }


def _empty_snapshot() -> RevlogMetricsSnapshot:
    return RevlogMetricsSnapshot(
        cards=CardsStudiedMetrics(),
        experience=ExperienceMetrics(),
        retention=RetentionMetrics(),
        streak=StreakMetrics(),
    )


def _day_start_ms(day_start: int, rollover_seconds: int) -> int:
    return (int(day_start) + int(rollover_seconds)) * 1000


def _ease(value: int | None) -> int:
    return max(1, min(4, _int(value, 1)))


def _int(value: object, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _int_at(values: list, index: int) -> int:
    if index >= len(values):
        return 0
    return max(0, _int(values[index]))


__all__ = ["RevlogMetricsSource", "RevlogMetricsSnapshot"]
