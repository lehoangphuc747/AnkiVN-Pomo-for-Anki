"""Small data models shared by the Pomodoro Qt widgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


LAYOUT_UNDER = "under"
LAYOUT_SIDEBAR = "sidebar"
LAYOUT_CORNER = "corner"

VALID_LAYOUTS = {LAYOUT_UNDER, LAYOUT_SIDEBAR, LAYOUT_CORNER}

MODE_POMODORO = "pomodoro"
MODE_BREAK = "break"


@dataclass
class PomodoroSettings:
    layout: str = LAYOUT_UNDER
    pomodoro_minutes: int = 25
    break_minutes: int = 5
    auto_start_break: bool = True
    auto_start_pomodoro_after_break: bool = False
    language: str = "vi"
    corner_left: Optional[int] = None
    corner_top: Optional[int] = None

    @classmethod
    def from_config(cls, config: dict) -> "PomodoroSettings":
        layout = str(config.get("layout", LAYOUT_UNDER))
        if layout not in VALID_LAYOUTS:
            layout = LAYOUT_UNDER
        language = str(config.get("language") or "vi").strip().replace("_", "-").lower().split("-", 1)[0] or "vi"

        return cls(
            layout=layout,
            pomodoro_minutes=_clamp_int(config.get("pomodoro_minutes"), 25, 1, 180),
            break_minutes=_clamp_int(config.get("break_minutes"), 5, 1, 60),
            auto_start_break=bool(config.get("auto_start_break", True)),
            auto_start_pomodoro_after_break=bool(config.get("auto_start_pomodoro_after_break", False)),
            language=language,
            corner_left=_optional_int(config.get("corner_left")),
            corner_top=_optional_int(config.get("corner_top")),
        )

    def to_config(self) -> dict:
        return {
            "layout": self.layout,
            "pomodoro_minutes": self.pomodoro_minutes,
            "break_minutes": self.break_minutes,
            "auto_start_break": self.auto_start_break,
            "auto_start_pomodoro_after_break": self.auto_start_pomodoro_after_break,
            "language": self.language,
            "corner_left": self.corner_left,
            "corner_top": self.corner_top,
        }


@dataclass
class PomodoroTimerState:
    mode: str
    total_seconds: int
    time_left: int
    paused: bool
    started: bool = False

    @property
    def label(self) -> str:
        from .i18n import tr

        return tr("mode.break_time") if self.mode == MODE_BREAK else tr("mode.pomodoro")

    @property
    def accent(self) -> str:
        return "#739E73" if self.mode == MODE_BREAK else "#D94B43"

    @property
    def time_text(self) -> str:
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def progress(self) -> float:
        if self.total_seconds <= 0:
            return 0.0
        return max(0.0, min(1.0, self.time_left / self.total_seconds))


@dataclass
class TimerRuntimeState:
    mode: str = MODE_POMODORO
    total_seconds: int = 25 * 60
    time_left: int = 25 * 60
    paused: bool = True
    started: bool = False
    saved_at: str = ""

    @classmethod
    def from_dict(cls, data: object) -> "TimerRuntimeState":
        if not isinstance(data, dict):
            return cls()
        mode = MODE_BREAK if data.get("mode") == MODE_BREAK else MODE_POMODORO
        total_seconds = _clamp_int(data.get("total_seconds"), 25 * 60, 1, 24 * 60 * 60)
        time_left = _clamp_int(data.get("time_left"), total_seconds, 0, total_seconds)
        return cls(
            mode=mode,
            total_seconds=total_seconds,
            time_left=time_left,
            paused=bool(data.get("paused", True)),
            started=bool(data.get("started", False)),
            saved_at=str(data.get("saved_at") or ""),
        )

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "total_seconds": self.total_seconds,
            "time_left": self.time_left,
            "paused": self.paused,
            "started": self.started,
            "saved_at": self.saved_at,
        }


@dataclass
class StudySessionState:
    id: str
    started_at: str
    updated_at: str
    session_index: int = 1
    session_total: int = 4
    xp_current: int = 0
    xp_goal: int = 20
    cards: int = 0
    new_cards: int = 0
    review_cards: int = 0
    again_cards: int = 0
    hard_cards: int = 0
    good_cards: int = 0
    easy_cards: int = 0
    deck_id: Optional[int] = None
    deck_name: str = ""

    @classmethod
    def from_dict(cls, data: object) -> Optional["StudySessionState"]:
        if not isinstance(data, dict) or not data.get("id"):
            return None
        return cls(
            id=str(data.get("id") or ""),
            started_at=str(data.get("started_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
            session_index=_positive_int(data.get("session_index")),
            session_total=_clamp_int(data.get("session_total"), 4, 1, 12),
            xp_current=_clamp_int(data.get("xp_current"), 0, 0, 1_000_000),
            xp_goal=_clamp_int(data.get("xp_goal"), 20, 1, 1_000_000),
            cards=_clamp_int(data.get("cards"), 0, 0, 1_000_000),
            new_cards=_clamp_int(data.get("new_cards"), 0, 0, 1_000_000),
            review_cards=_clamp_int(data.get("review_cards"), 0, 0, 1_000_000),
            again_cards=_clamp_int(data.get("again_cards"), 0, 0, 1_000_000),
            hard_cards=_clamp_int(data.get("hard_cards"), 0, 0, 1_000_000),
            good_cards=_clamp_int(data.get("good_cards"), 0, 0, 1_000_000),
            easy_cards=_clamp_int(data.get("easy_cards"), 0, 0, 1_000_000),
            deck_id=_optional_int(data.get("deck_id")),
            deck_name=str(data.get("deck_name") or ""),
        )

    @property
    def retention(self) -> int:
        if self.cards <= 0:
            return 0
        retained = self.cards - self.again_cards
        return round(retained * 100 / self.cards)

    def to_metrics(
        self,
        streak_days: int = 0,
        longest_streak_days: int = 0,
        today_cards: int = 0,
        today_xp: int = 0,
        streak_start_date: str = "",
        today_reviews: int = 0,
        yesterday_reviews: int = 0,
        cutoff_hour: int = 4,
        seconds_until_cutoff: int = 0,
        total_xp: int = 0,
        level: int = 1,
        level_floor_xp: int = 0,
        next_level_xp: int = 20,
        xp_to_next_level: int = 20,
        level_progress: int = 0,
    ) -> "SessionMetrics":
        return SessionMetrics(
            session_index=self.session_index,
            session_total=self.session_total,
            xp_current=total_xp,
            xp_goal=next_level_xp,
            cards=self.cards,
            retention=self.retention,
            streak_days=streak_days,
            new_cards=self.new_cards,
            learning_cards=self.new_cards,
            review_cards=self.review_cards,
            relearning_cards=0,
            filtered_cards=0,
            again_cards=self.again_cards,
            hard_cards=self.hard_cards,
            good_cards=self.good_cards,
            easy_cards=self.easy_cards,
            longest_streak_days=longest_streak_days,
            today_cards=today_cards,
            today_xp=today_xp,
            streak_start_date=streak_start_date,
            today_reviews=today_reviews,
            yesterday_reviews=yesterday_reviews,
            cutoff_hour=cutoff_hour,
            seconds_until_cutoff=seconds_until_cutoff,
            session_cards=self.cards,
            session_retention=self.retention,
            session_xp=self.xp_current,
            total_xp=total_xp,
            level=level,
            level_floor_xp=level_floor_xp,
            next_level_xp=next_level_xp,
            xp_to_next_level=xp_to_next_level,
            level_progress=level_progress,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "session_index": self.session_index,
            "session_total": self.session_total,
            "xp_current": self.xp_current,
            "xp_goal": self.xp_goal,
            "cards": self.cards,
            "new_cards": self.new_cards,
            "review_cards": self.review_cards,
            "again_cards": self.again_cards,
            "hard_cards": self.hard_cards,
            "good_cards": self.good_cards,
            "easy_cards": self.easy_cards,
            "deck_id": self.deck_id,
            "deck_name": self.deck_name,
        }


@dataclass
class SessionHistoryEntry:
    mode: str = MODE_POMODORO
    session_index: int = 1
    session_total: int = 4
    started_at: str = ""
    ended_at: str = ""
    duration_seconds: int = 0
    cards: int = 0
    xp: int = 0
    retention: int = 0
    completed: bool = False
    deck_name: str = ""

    @classmethod
    def from_dict(cls, data: object) -> Optional["SessionHistoryEntry"]:
        if not isinstance(data, dict):
            return None
        mode = MODE_BREAK if data.get("mode") == MODE_BREAK else MODE_POMODORO
        return cls(
            mode=mode,
            session_index=_positive_int(data.get("session_index")),
            session_total=_clamp_int(data.get("session_total"), 4, 1, 12),
            started_at=str(data.get("started_at") or ""),
            ended_at=str(data.get("ended_at") or ""),
            duration_seconds=_clamp_int(data.get("duration_seconds"), 0, 0, 24 * 60 * 60),
            cards=_clamp_int(data.get("cards"), 0, 0, 1_000_000),
            xp=_clamp_int(data.get("xp"), 0, 0, 1_000_000),
            retention=_clamp_int(data.get("retention"), 0, 0, 100),
            completed=bool(data.get("completed", False)),
            deck_name=str(data.get("deck_name") or ""),
        )

    @classmethod
    def from_session(
        cls,
        session: StudySessionState,
        mode: str,
        ended_at: str,
        duration_seconds: int,
        completed: bool,
    ) -> "SessionHistoryEntry":
        return cls(
            mode=MODE_BREAK if mode == MODE_BREAK else MODE_POMODORO,
            session_index=session.session_index,
            session_total=session.session_total,
            started_at=session.started_at,
            ended_at=ended_at,
            duration_seconds=max(0, int(duration_seconds)),
            cards=session.cards,
            xp=session.xp_current,
            retention=session.retention,
            completed=completed,
            deck_name=session.deck_name,
        )

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "session_index": self.session_index,
            "session_total": self.session_total,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "cards": self.cards,
            "xp": self.xp,
            "retention": self.retention,
            "completed": self.completed,
            "deck_name": self.deck_name,
        }


@dataclass
class SessionMetrics:
    session_index: int = 1
    session_total: int = 4
    xp_current: int = 0
    xp_goal: int = 20
    cards: int = 0
    retention: int = 0
    streak_days: int = 0
    new_cards: int = 0
    learning_cards: int = 0
    review_cards: int = 0
    relearning_cards: int = 0
    filtered_cards: int = 0
    again_cards: int = 0
    hard_cards: int = 0
    good_cards: int = 0
    easy_cards: int = 0
    longest_streak_days: int = 0
    today_cards: int = 0
    today_xp: int = 0
    streak_start_date: str = ""
    today_reviews: int = 0
    yesterday_reviews: int = 0
    cutoff_hour: int = 4
    seconds_until_cutoff: int = 0
    session_cards: int = 0
    session_retention: int = 0
    session_xp: int = 0
    total_xp: int = 0
    level: int = 1
    level_floor_xp: int = 0
    next_level_xp: int = 20
    xp_to_next_level: int = 20
    level_progress: int = 0


def _clamp_int(value: object, fallback: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(minimum, min(maximum, parsed))


def _positive_int(value: object, fallback: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = fallback
    return max(1, parsed)


def _optional_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
