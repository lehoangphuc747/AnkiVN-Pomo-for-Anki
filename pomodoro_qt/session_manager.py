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
from .experience_metric import XP_PER_COMPLETED_POMODORO, answer_experience, level_state
from .storage import PomodoroDataStore
from .tracking import ReviewAnswerEvent


SESSION_TOTAL = 4
MAX_HISTORY_ITEMS = 40
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
        total_xp = self._coerce_non_negative(source.get("total_xp"))
        level = level_state(total_xp)
        return SessionMetrics(
            session_index=session.session_index,
            session_total=session.session_total,
            xp_current=total_xp,
            xp_goal=level["next_level_xp"],
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
        xp = answer_experience(ease)
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
        if self._analytics_store is not None:
            self._analytics_store.add_session_xp(
                session,
                xp=XP_PER_COMPLETED_POMODORO,
                updated_at=_now_iso(),
                day=_today_key(),
            )
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
            today_entries = self._analytics_store.session_history_for_day(today_key)
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
            return self._analytics_store.metrics_source(session)
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
            "total_xp": 0,
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
