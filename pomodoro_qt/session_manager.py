"""Session lifecycle and study metric aggregation."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import uuid4

from .models import (
    DailyActivity,
    MODE_BREAK,
    MODE_POMODORO,
    SessionHistoryEntry,
    SessionMetrics,
    StudySessionState,
    TimerRuntimeState,
)
from .storage import PomodoroDataStore
from .tracking import CARD_KIND_NEW, ReviewAnswerEvent


SESSION_TOTAL = 4
MAX_HISTORY_ITEMS = 40
MAX_DAILY_STATS_DAYS = 180
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

    def __init__(self, store: PomodoroDataStore) -> None:
        self._store = store
        self._state = store.load()
        self.active_session = StudySessionState.from_dict(self._state.get("active_session"))
        self.history = self._load_history(self._state.get("history"))
        self.daily_stats = self._load_daily_stats(self._state.get("daily_stats"))
        self.total_xp = self._load_total_xp(self._state.get("total_xp"))
        self.session_index = self._coerce_session_index(self._state.get("session_index"))
        if self.active_session:
            self.session_index = self.active_session.session_index
        self.current_streak_days = self._coerce_non_negative(self._state.get("current_streak_days"))
        self.longest_streak_days = self._coerce_non_negative(self._state.get("longest_streak_days"))
        self._timer_state = TimerRuntimeState.from_dict(self._state.get("timer_state"))
        self._audio_state = self._state.get("audio_state") if isinstance(self._state.get("audio_state"), dict) else {}
        self._recompute_streaks()

    def metrics(self) -> SessionMetrics:
        session = self.active_session or self._empty_session()
        today = self.daily_stats.get(_today_key(), {})
        level = level_state(self.total_xp)
        return session.to_metrics(
            streak_days=self.current_streak_days,
            longest_streak_days=self.longest_streak_days,
            today_cards=self._coerce_non_negative(today.get("cards")),
            today_xp=self._coerce_non_negative(today.get("xp")),
            week_activity=self.week_activity(),
            total_xp=self.total_xp,
            level=level["level"],
            level_floor_xp=level["floor_xp"],
            next_level_xp=level["next_level_xp"],
            xp_to_next_level=level["xp_to_next_level"],
            level_progress=level["progress"],
        )

    def timer_state(self) -> TimerRuntimeState:
        return self._timer_state

    def save_timer_state(self, timer_state: TimerRuntimeState) -> None:
        self._timer_state = timer_state
        self.save()

    def audio_state(self) -> dict:
        return dict(self._audio_state)

    def save_audio_state(self, audio_state: dict) -> None:
        self._audio_state = dict(audio_state or {})
        self.save()

    def mark_timer_started(self, deck_id: Optional[int] = None, deck_name: str = "") -> SessionMetrics:
        self.ensure_active_session(deck_id, deck_name)
        self.save()
        return self.metrics()

    def record_answer(self, event: ReviewAnswerEvent) -> SessionMetrics:
        session = self.ensure_active_session(event.deck_id, event.deck_name)
        now = _now_iso()
        ease = max(1, min(4, int(event.ease or 1)))
        xp = XP_BY_EASE.get(ease, 0)

        session.cards += 1
        session.xp_current = max(0, session.xp_current + xp)
        self.total_xp = max(0, self.total_xp + xp)
        session.updated_at = now
        if event.deck_id is not None:
            session.deck_id = event.deck_id
        if event.deck_name:
            session.deck_name = event.deck_name

        if event.card_kind == CARD_KIND_NEW:
            session.new_cards += 1
        else:
            session.review_cards += 1

        if ease == 1:
            session.again_cards += 1
        elif ease == 2:
            session.hard_cards += 1
        elif ease == 3:
            session.good_cards += 1
        else:
            session.easy_cards += 1

        self._update_daily_stats(ease, xp)
        self._recompute_streaks()
        self.save()
        return self.metrics()

    def complete_pomodoro(self, duration_seconds: int) -> SessionMetrics:
        session = self.ensure_active_session()
        completed_metrics = self.metrics()
        self._append_history(session, MODE_POMODORO, duration_seconds, completed=True)
        self.session_index = self._next_session_index(session.session_index)
        self.active_session = None
        self.save()
        return completed_metrics

    def complete_break(self, duration_seconds: int) -> SessionMetrics:
        self.history.append(
            SessionHistoryEntry(
                mode=MODE_BREAK,
                session_index=self.session_index,
                session_total=SESSION_TOTAL,
                started_at="",
                ended_at=_now_iso(),
                duration_seconds=max(0, int(duration_seconds)),
                completed=True,
            )
        )
        self.history = self.history[-MAX_HISTORY_ITEMS:]
        self.save()
        return self.metrics()

    def stop_current_session(self, mode: str, duration_seconds: int) -> SessionMetrics:
        if self.active_session is not None and self._has_session_data(self.active_session):
            self._append_history(self.active_session, mode, duration_seconds, completed=False)
        self.active_session = None
        self.save()
        return self.metrics()

    def recent_history(self) -> list[SessionHistoryEntry]:
        return list(self.history[-MAX_HISTORY_ITEMS:])

    def today_history(self) -> list[SessionHistoryEntry]:
        today_key = _today_key()
        return [entry for entry in self.recent_history() if _date_key_from_iso(entry.ended_at) == today_key]

    def week_activity(self) -> tuple[DailyActivity, ...]:
        today = date.today()
        days = []
        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            key = day.isoformat()
            stats = self.daily_stats.get(key, {})
            days.append(
                DailyActivity(
                    label=day.strftime("%a"),
                    date=key,
                    cards=self._coerce_non_negative(stats.get("cards")),
                    xp=self._coerce_non_negative(stats.get("xp")),
                )
            )
        return tuple(days)

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

    def save(self) -> None:
        self._prune_daily_stats()
        self._store.save(
            {
                "active_session": self.active_session.to_dict() if self.active_session else None,
                "timer_state": self._timer_state.to_dict() if self._timer_state else None,
                "history": [entry.to_dict() for entry in self.history[-MAX_HISTORY_ITEMS:]],
                "daily_stats": self.daily_stats,
                "total_xp": self.total_xp,
                "session_index": self.session_index,
                "current_streak_days": self.current_streak_days,
                "longest_streak_days": self.longest_streak_days,
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

    def _append_history(self, session: StudySessionState, mode: str, duration_seconds: int, completed: bool) -> None:
        self.history.append(
            SessionHistoryEntry.from_session(
                session=session,
                mode=mode,
                ended_at=_now_iso(),
                duration_seconds=duration_seconds,
                completed=completed,
            )
        )
        self.history = self.history[-MAX_HISTORY_ITEMS:]

    def _update_daily_stats(self, ease: int, xp: int) -> None:
        key = _today_key()
        stats = self.daily_stats.setdefault(key, {})
        stats["cards"] = self._coerce_non_negative(stats.get("cards")) + 1
        stats["xp"] = max(0, self._coerce_non_negative(stats.get("xp")) + xp)
        stats["again"] = self._coerce_non_negative(stats.get("again")) + (1 if ease == 1 else 0)
        stats["hard"] = self._coerce_non_negative(stats.get("hard")) + (1 if ease == 2 else 0)
        stats["good"] = self._coerce_non_negative(stats.get("good")) + (1 if ease == 3 else 0)
        stats["easy"] = self._coerce_non_negative(stats.get("easy")) + (1 if ease == 4 else 0)

    def _recompute_streaks(self) -> None:
        today = date.today()
        end_day = today
        if not self._has_activity_on(end_day) and self._has_activity_on(today - timedelta(days=1)):
            end_day = today - timedelta(days=1)

        streak = 0
        cursor = end_day
        while self._has_activity_on(cursor):
            streak += 1
            cursor -= timedelta(days=1)

        self.current_streak_days = streak
        self.longest_streak_days = max(self.longest_streak_days, self._compute_longest_streak())

    def _compute_longest_streak(self) -> int:
        active_days = sorted(key for key, stats in self.daily_stats.items() if self._coerce_non_negative(stats.get("cards")) > 0)
        longest = 0
        current = 0
        previous: Optional[date] = None
        for key in active_days:
            try:
                day = date.fromisoformat(key)
            except ValueError:
                continue
            if previous is None or day == previous + timedelta(days=1):
                current += 1
            else:
                current = 1
            longest = max(longest, current)
            previous = day
        return longest

    def _has_activity_on(self, day: date) -> bool:
        stats = self.daily_stats.get(day.isoformat(), {})
        return self._coerce_non_negative(stats.get("cards")) > 0

    def _prune_daily_stats(self) -> None:
        if len(self.daily_stats) <= MAX_DAILY_STATS_DAYS:
            return
        keep_keys = sorted(self.daily_stats.keys())[-MAX_DAILY_STATS_DAYS:]
        self.daily_stats = {key: self.daily_stats[key] for key in keep_keys}

    def _next_session_index(self, current_index: int) -> int:
        if current_index >= SESSION_TOTAL:
            return 1
        return current_index + 1

    def _has_session_data(self, session: StudySessionState) -> bool:
        return session.cards > 0 or session.xp_current > 0

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

    def _load_total_xp(self, value: object) -> int:
        total_xp = self._coerce_non_negative(value)
        if total_xp > 0:
            return total_xp
        if self._coerce_non_negative(self._state.get("_loaded_version")) < 2:
            return sum(self._coerce_non_negative(stats.get("xp")) for stats in self.daily_stats.values())
        return 0

    def _coerce_session_index(self, value: object) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 1
        return max(1, min(SESSION_TOTAL, parsed))

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
