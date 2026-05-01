"""Session lifecycle and study metric aggregation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from .models import (
    MODE_BREAK,
    MODE_POMODORO,
    SessionHistoryEntry,
    SessionMetrics,
    StudySessionState,
    TimerRuntimeState,
)
from .analytics_store import PomodoroAnalyticsStore
from .storage import PomodoroDataStore
from .tracking import ReviewAnswerEvent


SESSION_TOTAL = 4
MAX_HISTORY_ITEMS = 40
XP_BY_EASE = {
    1: -1,
    2: 1,
    3: 2,
    4: 1,
}
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


class PomodoroSessionManager:
    """Owns non-UI Pomodoro state for the active Anki profile."""

    def __init__(self, store: PomodoroDataStore, analytics_store: Optional[PomodoroAnalyticsStore] = None) -> None:
        self._store = store
        self._analytics_store = analytics_store
        self._state = store.load()
        self.active_session = StudySessionState.from_dict(self._state.get("active_session"))
        legacy_history = self._load_history(self._state.get("history"))
        legacy_daily_stats = self._load_daily_stats(self._state.get("daily_stats"))
        self.session_index = self._coerce_session_index(self._state.get("session_index"))
        if self.active_session:
            self.session_index = self.active_session.session_index
        self._timer_state = TimerRuntimeState.from_dict(self._state.get("timer_state"))
        self._audio_state = self._state.get("audio_state") if isinstance(self._state.get("audio_state"), dict) else {}
        if self._analytics_store is not None:
            self._analytics_store.bootstrap_from_json(legacy_history, legacy_daily_stats, self.active_session)

    def metrics(self) -> SessionMetrics:
        session = self.active_session or self._empty_session()
        source = self._metrics_source(session)
        session_progress = source["progress"]
        today_progress = source.get("today_progress") or session_progress
        total_xp = self._coerce_non_negative(source.get("total_xp"))
        level = level_state(total_xp)
        return SessionMetrics(
            session_index=session.session_index,
            session_total=session.session_total,
            xp_current=total_xp,
            xp_goal=level["next_level_xp"],
            cards=self._coerce_non_negative(today_progress.get("cards")),
            retention=_retention_from_progress(today_progress),
            streak_days=self._coerce_non_negative(source.get("streak_days")),
            new_cards=self._coerce_non_negative(today_progress.get("new_cards")),
            learning_cards=self._coerce_non_negative(today_progress.get("learning_cards")),
            review_cards=self._coerce_non_negative(today_progress.get("review_cards")),
            relearning_cards=self._coerce_non_negative(today_progress.get("relearning_cards")),
            filtered_cards=self._coerce_non_negative(today_progress.get("filtered_cards")),
            again_cards=self._coerce_non_negative(today_progress.get("again_cards")),
            hard_cards=self._coerce_non_negative(today_progress.get("hard_cards")),
            good_cards=self._coerce_non_negative(today_progress.get("good_cards")),
            easy_cards=self._coerce_non_negative(today_progress.get("easy_cards")),
            longest_streak_days=self._coerce_non_negative(source.get("longest_streak_days")),
            today_cards=self._coerce_non_negative(source.get("today_cards")),
            today_xp=self._coerce_non_negative(source.get("today_xp")),
            streak_start_date=str(source.get("streak_start_date") or ""),
            today_reviews=self._coerce_non_negative(source.get("today_reviews")),
            yesterday_reviews=self._coerce_non_negative(source.get("yesterday_reviews")),
            cutoff_hour=(
                self._coerce_non_negative(source.get("cutoff_hour")) if source.get("cutoff_hour") is not None else 4
            ),
            seconds_until_cutoff=self._coerce_non_negative(source.get("seconds_until_cutoff")),
            session_cards=self._coerce_non_negative(session_progress.get("cards")),
            session_retention=_retention_from_progress(session_progress),
            session_xp=self._coerce_non_negative(session_progress.get("xp")),
            total_xp=total_xp,
            level=level["level"],
            level_floor_xp=level["floor_xp"],
            next_level_xp=level["next_level_xp"],
            xp_to_next_level=level["xp_to_next_level"],
            level_progress=level["progress"],
        )

    def timer_state(self) -> TimerRuntimeState:
        return self._timer_state

    def save_timer_state(self, timer_state: TimerRuntimeState) -> bool:
        self._timer_state = timer_state
        return self.save()

    def audio_state(self) -> dict:
        return dict(self._audio_state)

    def save_audio_state(self, audio_state: dict) -> bool:
        self._audio_state = dict(audio_state or {})
        return self.save()

    def mark_timer_started(self, deck_id: Optional[int] = None, deck_name: str = "") -> SessionMetrics:
        session = self.ensure_active_session(deck_id, deck_name)
        if self._analytics_store is not None:
            self._analytics_store.seed_session_progress(session)
        self.save()
        return self.metrics()

    def record_answer(self, event: ReviewAnswerEvent) -> SessionMetrics:
        session = self.ensure_active_session(event.deck_id, event.deck_name)
        now = _now_iso()
        ease = max(1, min(4, int(event.ease or 1)))
        xp = XP_BY_EASE.get(ease, 0)
        session.updated_at = now
        if event.deck_id is not None:
            session.deck_id = event.deck_id
        if event.deck_name:
            session.deck_name = event.deck_name
        if self._analytics_store is not None:
            self._analytics_store.record_answer(
                answered_at=now,
                session=session,
                card_id=event.card_id,
                ease=ease,
                card_kind=event.card_kind,
                deck_id=event.deck_id,
                deck_name=event.deck_name,
                xp=xp,
                day=_today_key(),
            )
        self.save()
        return self.metrics()

    def complete_pomodoro(self, duration_seconds: int) -> SessionMetrics:
        session = self.ensure_active_session()
        completed_metrics = self.metrics()
        if self._analytics_store is not None:
            self._analytics_store.finalize_session(
                session,
                mode=MODE_POMODORO,
                ended_at=_now_iso(),
                duration_seconds=duration_seconds,
                completed=True,
            )
        self.session_index = self._next_session_index(session.session_index)
        self.active_session = None
        self.save()
        return completed_metrics

    def complete_break(self, duration_seconds: int) -> SessionMetrics:
        entry = SessionHistoryEntry(
            mode=MODE_BREAK,
            session_index=self.session_index,
            session_total=SESSION_TOTAL,
            started_at="",
            ended_at=_now_iso(),
            duration_seconds=max(0, int(duration_seconds)),
            completed=True,
        )
        if self._analytics_store is not None:
            self._analytics_store.record_session(entry)
        self.save()
        return self.metrics()

    def stop_current_session(self, mode: str, duration_seconds: int) -> SessionMetrics:
        if self.active_session is not None and self._has_session_data(self.active_session):
            if self._analytics_store is not None:
                self._analytics_store.finalize_session(
                    self.active_session,
                    mode=mode,
                    ended_at=_now_iso(),
                    duration_seconds=duration_seconds,
                    completed=False,
                )
        self.active_session = None
        self.save()
        return self.metrics()

    def recent_history(self) -> list[SessionHistoryEntry]:
        if self._analytics_store is not None:
            return self._analytics_store.session_history(max_rows=MAX_HISTORY_ITEMS)
        return []

    def history_for_popover(self) -> list[SessionHistoryEntry]:
        if self._analytics_store is not None:
            return self._analytics_store.session_history()
        return []

    def history_popover_snapshot(self) -> dict:
        today_key = _today_key()
        if self._analytics_store is not None:
            today_entries = self._analytics_store.session_history_for_day(today_key, max_rows=12)
            day_summaries = self._analytics_store.history_day_summaries(limit_days=60)
            return {"today": today_entries, "days": day_summaries}
        return {"today": [], "days": []}

    def today_history(self) -> list[SessionHistoryEntry]:
        today_key = _today_key()
        if self._analytics_store is not None:
            return self._analytics_store.session_history_for_day(today_key)
        return []

    def ensure_active_session(self, deck_id: Optional[int] = None, deck_name: str = "") -> StudySessionState:
        if self.active_session is None:
            now = _now_iso()
            self.active_session = StudySessionState(
                id=uuid4().hex,
                started_at=now,
                updated_at=now,
                session_index=self.session_index,
                session_total=SESSION_TOTAL,
                deck_id=deck_id,
                deck_name=deck_name,
            )
        else:
            if deck_id is not None:
                self.active_session.deck_id = deck_id
            if deck_name:
                self.active_session.deck_name = deck_name
        return self.active_session

    def save(self) -> bool:
        return self._store.save(
            {
                "active_session": self.active_session.to_dict() if self.active_session else None,
                "timer_state": self._timer_state.to_dict() if self._timer_state else None,
                "history": [],
                "daily_stats": {},
                "total_xp": 0,
                "session_index": self.session_index,
                "current_streak_days": 0,
                "longest_streak_days": 0,
                "audio_state": self._audio_state,
            }
        )

    def _empty_session(self) -> StudySessionState:
        return StudySessionState(
            id="",
            started_at="",
            updated_at="",
            session_index=self.session_index,
            session_total=SESSION_TOTAL,
        )

    def _next_session_index(self, current_index: int) -> int:
        try:
            parsed = int(current_index)
        except (TypeError, ValueError):
            parsed = 1
        return max(1, parsed) + 1

    def _has_session_data(self, session: StudySessionState) -> bool:
        if self._analytics_store is not None:
            return self._analytics_store.has_session_progress_data(session.id)
        return False

    def _metrics_source(self, session: StudySessionState) -> dict:
        if self._analytics_store is not None:
            return self._analytics_store.metrics_source(session, _today_key())
        return {
            "progress": {
                "cards": 0,
                "new_cards": 0,
                "learning_cards": 0,
                "review_cards": 0,
                "relearning_cards": 0,
                "filtered_cards": 0,
                "again_cards": 0,
                "hard_cards": 0,
                "good_cards": 0,
                "easy_cards": 0,
                "xp": 0,
            },
            "today_progress": {
                "cards": 0,
                "new_cards": 0,
                "learning_cards": 0,
                "review_cards": 0,
                "relearning_cards": 0,
                "filtered_cards": 0,
                "again_cards": 0,
                "hard_cards": 0,
                "good_cards": 0,
                "easy_cards": 0,
                "xp": 0,
            },
            "today_cards": 0,
            "today_xp": 0,
            "total_xp": 0,
            "streak_days": 0,
            "longest_streak_days": 0,
            "streak_start_date": "",
            "today_reviews": 0,
            "yesterday_reviews": 0,
            "cutoff_hour": 4,
            "seconds_until_cutoff": 0,
        }

    def _load_history(self, raw_history: object) -> list[SessionHistoryEntry]:
        if not isinstance(raw_history, list):
            return []
        entries = []
        for item in raw_history:
            entry = SessionHistoryEntry.from_dict(item)
            if entry:
                entries.append(entry)
        return entries[-MAX_HISTORY_ITEMS:]

    def _load_daily_stats(self, raw_stats: object) -> dict:
        if not isinstance(raw_stats, dict):
            return {}
        clean = {}
        for key, value in raw_stats.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                continue
            clean[key] = {
                "cards": self._coerce_non_negative(value.get("cards")),
                "xp": self._coerce_non_negative(value.get("xp")),
                "again": self._coerce_non_negative(value.get("again")),
                "hard": self._coerce_non_negative(value.get("hard")),
                "good": self._coerce_non_negative(value.get("good")),
                "easy": self._coerce_non_negative(value.get("easy")),
            }
        return clean

    def _coerce_session_index(self, value: object) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 1
        return max(1, parsed)

    def _coerce_non_negative(self, value: object) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, parsed)


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _today_key() -> str:
    return date.today().isoformat()


def _date_key_from_iso(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return ""
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone()
    return parsed.date().isoformat()


def _summaries_from_history(history: list[SessionHistoryEntry]) -> list[dict]:
    summaries: dict[str, dict] = {}
    for entry in history:
        day = _date_key_from_iso(entry.ended_at)
        if not day:
            continue
        summary = summaries.setdefault(
            day,
            {"day": day, "pomodoros": 0, "breaks": 0, "cards": 0, "xp": 0, "duration_seconds": 0},
        )
        if entry.mode == MODE_BREAK:
            summary["breaks"] += 1
        else:
            summary["pomodoros"] += 1
        summary["cards"] += max(0, entry.cards)
        summary["xp"] += max(0, entry.xp)
        summary["duration_seconds"] += max(0, entry.duration_seconds)
    return [summaries[key] for key in sorted(summaries.keys(), reverse=True)]


def _retention_from_progress(progress: dict) -> int:
    cards = _non_negative(progress.get("cards"))
    if cards <= 0:
        return 0
    again = _non_negative(progress.get("again_cards"))
    return round((cards - again) * 100 / cards)


def _non_negative(value: object) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def level_state(total_xp: int) -> dict:
    total_xp = max(0, int(total_xp))
    level = 1
    while _level_threshold(level + 1) <= total_xp:
        level += 1

    floor_xp = _level_threshold(level)
    next_level_xp = _level_threshold(level + 1)
    span = max(1, next_level_xp - floor_xp)
    earned_in_level = max(0, total_xp - floor_xp)
    return {
        "level": level,
        "floor_xp": floor_xp,
        "next_level_xp": next_level_xp,
        "xp_to_next_level": max(0, next_level_xp - total_xp),
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
