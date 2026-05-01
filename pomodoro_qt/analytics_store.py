"""SQLite-backed long-term analytics storage for Pomodoro data."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from hashlib import sha1
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional
from uuid import uuid4

from .models import MODE_BREAK, MODE_POMODORO, SessionHistoryEntry, StudySessionState


DB_FILENAME = "pomodoro_qt.db"
SCHEMA_VERSION = 2
JSON_MIGRATION_KEY = "json_migration_v1"


class PomodoroAnalyticsStore:
    """Stores dashboard-friendly long-term data outside the runtime JSON state."""

    def __init__(self, mw: Any, addon_package: str) -> None:
        self._mw = mw
        self._addon_package = addon_package
        self.path = self._resolve_path()
        self.last_error: Exception | None = None
        self.last_streak_debug: dict[str, Any] = {}
        self._anki_streak_cache: dict[str, Any] | None = None
        self._anki_streak_cache_today: int | None = None
        self._ensure_schema()

    def bootstrap_from_json(
        self,
        history: Iterable[SessionHistoryEntry],
        daily_stats: dict,
        active_session: StudySessionState | None = None,
    ) -> None:
        if self._meta(JSON_MIGRATION_KEY) == "done":
            if active_session is not None:
                self.seed_session_progress(active_session)
            return
        try:
            with self._connection() as db:
                for index, entry in enumerate(history):
                    self._insert_session(db, _migration_session_id(index, entry), entry)
                for day, stats in daily_stats.items():
                    self._upsert_daily_stats(db, str(day), stats)
                if active_session is not None:
                    self._seed_session_progress(db, active_session)
                self._set_meta(db, JSON_MIGRATION_KEY, "done")
            self.last_error = None
        except Exception as exc:
            self._handle_error("bootstrap", exc)

    def seed_session_progress(self, session: StudySessionState) -> None:
        if not session.id:
            return
        try:
            with self._connection() as db:
                self._seed_session_progress(db, session)
            self.last_error = None
        except Exception as exc:
            self._handle_error("seed_session_progress", exc)

    def record_answer(
        self,
        *,
        answered_at: str,
        session: StudySessionState,
        card_id: int,
        ease: int,
        card_kind: str,
        deck_id: Optional[int],
        deck_name: str,
        xp: int,
        day: str,
    ) -> None:
        try:
            ease = max(1, min(4, int(ease or 1)))
            with self._connection() as db:
                self._ensure_session_progress(db, session)
                db.execute(
                    """
                    INSERT INTO review_events (
                        answered_at, session_id, card_id, ease, card_kind, deck_id, deck_name, xp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (answered_at, session.id, int(card_id), ease, card_kind, deck_id, deck_name, int(xp)),
                )
                db.execute(
                    """
                    UPDATE session_progress
                    SET updated_at = ?,
                        cards = cards + 1,
                        new_cards = new_cards + ?,
                        review_cards = review_cards + ?,
                        again_cards = again_cards + ?,
                        hard_cards = hard_cards + ?,
                        good_cards = good_cards + ?,
                        easy_cards = easy_cards + ?,
                        xp = MAX(0, xp + ?),
                        deck_id = COALESCE(?, deck_id),
                        deck_name = CASE WHEN ? != '' THEN ? ELSE deck_name END
                    WHERE session_id = ?
                    """,
                    (
                        answered_at,
                        1 if card_kind == "new" else 0,
                        0 if card_kind == "new" else 1,
                        1 if ease == 1 else 0,
                        1 if ease == 2 else 0,
                        1 if ease == 3 else 0,
                        1 if ease == 4 else 0,
                        int(xp),
                        deck_id,
                        deck_name,
                        deck_name,
                        session.id,
                    ),
                )
                self._increment_daily_stats(db, day, ease, int(xp))
            self._note_anki_review_answered()
            self.last_error = None
        except Exception as exc:
            self._handle_error("record_answer", exc)

    def metrics_source(self, session: StudySessionState, today: str) -> dict[str, Any]:
        review_streaks = self._anki_review_streaks()
        try:
            with self._connection() as db:
                progress = self._session_progress_row(db, session)
                total_xp = _int(db.execute("SELECT COALESCE(SUM(xp), 0) FROM daily_stats").fetchone()[0], 0)
            today_progress = self._anki_today_review_progress()
            self.last_error = None
            return {
                "progress": progress,
                "today_progress": today_progress,
                "today_cards": review_streaks["today_cards"],
                "today_xp": review_streaks["today_xp"],
                "total_xp": total_xp,
                "streak_days": review_streaks["streak_days"],
                "longest_streak_days": review_streaks["longest_streak_days"],
                "streak_start_date": review_streaks["streak_start_date"],
                "today_reviews": review_streaks["today_reviews"],
                "yesterday_reviews": review_streaks["yesterday_reviews"],
                "cutoff_hour": review_streaks["cutoff_hour"],
                "seconds_until_cutoff": review_streaks["seconds_until_cutoff"],
            }
        except Exception as exc:
            self._handle_error("metrics_source", exc)
            return {
                "progress": _progress_from_session(session),
                "today_progress": self._anki_today_review_progress(),
                "today_cards": review_streaks["today_cards"],
                "today_xp": review_streaks["today_xp"],
                "total_xp": 0,
                "streak_days": review_streaks["streak_days"],
                "longest_streak_days": review_streaks["longest_streak_days"],
                "streak_start_date": review_streaks["streak_start_date"],
                "today_reviews": review_streaks["today_reviews"],
                "yesterday_reviews": review_streaks["yesterday_reviews"],
                "cutoff_hour": review_streaks["cutoff_hour"],
                "seconds_until_cutoff": review_streaks["seconds_until_cutoff"],
            }

    def _anki_today_review_progress(self) -> dict[str, Any]:
        try:
            col = getattr(self._mw, "col", None)
            db = getattr(col, "db", None)
            if db is None:
                return _empty_progress()
            rollover_seconds = _anki_rollover_seconds(col)
            anki_today = _anki_today_start(db, rollover_seconds)
            start_ms = (int(anki_today) + int(rollover_seconds)) * 1000
            end_ms = start_ms + 86400 * 1000
            row = db.first(
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
            progress = _progress_from_sequence(row)
            progress["new_cards"] = progress["learning_cards"]
            progress["xp"] = _xp_from_progress(progress)
            return progress
        except Exception as exc:
            self._handle_error("anki_today_review_progress", exc)
            return _empty_progress()

    def _anki_review_streaks(self) -> dict[str, Any]:
        try:
            col = getattr(self._mw, "col", None)
            db = getattr(col, "db", None)
            if db is None:
                return _empty_anki_review_streaks()
            rollover_seconds = _anki_rollover_seconds(col)
            anki_today = _anki_today_start(db, rollover_seconds)
            if self._anki_streak_cache is not None and self._anki_streak_cache_today == anki_today:
                return self._cached_anki_review_streaks(anki_today, rollover_seconds)
            rollover_hours = rollover_seconds / 3600
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
            reviews_by_day = {_int(day, 0): _int(reviews, 0) for day, reviews in rows if day is not None}
            active_days = sorted(day for day, reviews in reviews_by_day.items() if reviews > 0)
            streak_days = _current_streak_days(active_days, anki_today)
            streak_end_day = _current_streak_end_day(active_days, anki_today)
            streak_start_day = _streak_start_day(streak_end_day, streak_days)
            longest_streak_days = _longest_streak_days(active_days)
            today_reviews = max(0, reviews_by_day.get(anki_today, 0))
            yesterday_reviews = max(0, reviews_by_day.get(anki_today - 86400, 0))
            cutoff_hour = max(0, min(23, int(rollover_seconds) // 3600))
            seconds_until_cutoff = _seconds_until_cutoff(anki_today, rollover_seconds)
            self.last_streak_debug = {
                "rollover_hours": rollover_hours,
                "today": anki_today,
                "today_key": _day_key(anki_today),
                "today_reviews": today_reviews,
                "yesterday_reviews": yesterday_reviews,
                "last_active_day": _day_key(active_days[-1]) if active_days else None,
                "streak_days": streak_days,
                "streak_start_date": _day_key(streak_start_day) if streak_start_day is not None else "",
                "longest_streak_days": longest_streak_days,
                "active_days": len(active_days),
            }
            result = {
                "streak_days": streak_days,
                "longest_streak_days": longest_streak_days,
                "streak_start_date": _day_key(streak_start_day) if streak_start_day is not None else "",
                "today_cards": today_reviews,
                "today_xp": 0,
                "today_reviews": today_reviews,
                "yesterday_reviews": yesterday_reviews,
                "cutoff_hour": cutoff_hour,
                "seconds_until_cutoff": seconds_until_cutoff,
            }
            self._anki_streak_cache = dict(result)
            self._anki_streak_cache_today = anki_today
            return result
        except Exception as exc:
            self.last_streak_debug = {"error": f"{type(exc).__name__}: {exc}"}
            self._handle_error("anki_review_streaks", exc)
            return _empty_anki_review_streaks()

    def _cached_anki_review_streaks(self, anki_today: int, rollover_seconds: int) -> dict[str, Any]:
        cached = dict(self._anki_streak_cache or _empty_anki_review_streaks())
        cached["seconds_until_cutoff"] = _seconds_until_cutoff(anki_today, rollover_seconds)
        cutoff_hour = max(0, min(23, int(rollover_seconds) // 3600))
        cached["cutoff_hour"] = cutoff_hour
        self.last_streak_debug = {
            "cached": True,
            "today": anki_today,
            "today_key": _day_key(anki_today),
            "today_reviews": cached["today_reviews"],
            "yesterday_reviews": cached["yesterday_reviews"],
            "streak_days": cached["streak_days"],
            "streak_start_date": cached["streak_start_date"],
            "longest_streak_days": cached["longest_streak_days"],
        }
        self._anki_streak_cache = dict(cached)
        return cached

    def _note_anki_review_answered(self) -> None:
        if self._anki_streak_cache is None:
            return
        try:
            col = getattr(self._mw, "col", None)
            db = getattr(col, "db", None)
            if db is None:
                self._anki_streak_cache = None
                self._anki_streak_cache_today = None
                return
            rollover_seconds = _anki_rollover_seconds(col)
            anki_today = _anki_today_start(db, rollover_seconds)
            if self._anki_streak_cache_today != anki_today:
                self._anki_streak_cache = None
                self._anki_streak_cache_today = None
                return
            today_reviews = _int(self._anki_streak_cache.get("today_reviews"), 0) + 1
            self._anki_streak_cache["today_reviews"] = today_reviews
            self._anki_streak_cache["today_cards"] = today_reviews
            if _int(self._anki_streak_cache.get("streak_days"), 0) <= 0:
                self._anki_streak_cache["streak_days"] = 1
                self._anki_streak_cache["streak_start_date"] = _day_key(anki_today)
            self._anki_streak_cache["longest_streak_days"] = max(
                _int(self._anki_streak_cache.get("longest_streak_days"), 0),
                _int(self._anki_streak_cache.get("streak_days"), 0),
            )
        except Exception:
            self._anki_streak_cache = None
            self._anki_streak_cache_today = None

    def finalize_session(
        self,
        session: StudySessionState,
        *,
        mode: str,
        ended_at: str,
        duration_seconds: int,
        completed: bool,
    ) -> SessionHistoryEntry:
        try:
            with self._connection() as db:
                progress = self._session_progress_row(db, session)
                entry = _entry_from_progress(session, progress, mode, ended_at, duration_seconds, completed)
                self._insert_session(db, session.id, entry)
                db.execute("DELETE FROM session_progress WHERE session_id = ?", (session.id,))
            self.last_error = None
            return entry
        except Exception as exc:
            self._handle_error("finalize_session", exc)
            return SessionHistoryEntry.from_session(session, mode, ended_at, duration_seconds, completed)

    def has_session_progress_data(self, session_id: str) -> bool:
        try:
            with self._connection() as db:
                row = db.execute("SELECT cards, xp FROM session_progress WHERE session_id = ?", (session_id,)).fetchone()
            self.last_error = None
            return bool(row and (_int(row["cards"], 0) > 0 or _int(row["xp"], 0) > 0))
        except Exception as exc:
            self._handle_error("has_session_progress_data", exc)
            return False

    def clear_session_progress(self, session_id: str) -> None:
        try:
            with self._connection() as db:
                db.execute("DELETE FROM session_progress WHERE session_id = ?", (session_id,))
            self.last_error = None
        except Exception as exc:
            self._handle_error("clear_session_progress", exc)

    def record_session(self, entry: SessionHistoryEntry, session_id: Optional[str] = None) -> None:
        try:
            with self._connection() as db:
                self._insert_session(db, session_id or uuid4().hex, entry)
            self.last_error = None
        except Exception as exc:
            self._handle_error("record_session", exc)

    def session_history(self, limit_days: int = 180, max_rows: int = 1000) -> list[SessionHistoryEntry]:
        try:
            limit_days = max(1, int(limit_days))
            max_rows = max(1, int(max_rows))
            with self._connection() as db:
                rows = _rows(
                    db.execute(
                        """
                        SELECT mode, session_index, session_total, started_at, ended_at,
                               duration_seconds, cards, xp, retention, completed, deck_name
                        FROM sessions
                        WHERE ended_at >= date('now', ?)
                        ORDER BY ended_at DESC, id DESC
                        LIMIT ?
                        """,
                        (f"-{limit_days - 1} days", max_rows),
                    )
                )
            entries = []
            for row in rows:
                entry = SessionHistoryEntry.from_dict(row)
                if entry is not None:
                    entries.append(entry)
            self.last_error = None
            return entries
        except Exception as exc:
            self._handle_error("session_history", exc)
            return []

    def session_history_for_day(self, day: str, max_rows: int = 12) -> list[SessionHistoryEntry]:
        try:
            max_rows = max(1, int(max_rows))
            with self._connection() as db:
                rows = _rows(
                    db.execute(
                        """
                        SELECT mode, session_index, session_total, started_at, ended_at,
                               duration_seconds, cards, xp, retention, completed, deck_name
                        FROM sessions
                        WHERE substr(ended_at, 1, 10) = ?
                        ORDER BY ended_at DESC, id DESC
                        LIMIT ?
                        """,
                        (str(day), max_rows),
                    )
                )
            entries = []
            for row in rows:
                entry = SessionHistoryEntry.from_dict(row)
                if entry is not None:
                    entries.append(entry)
            self.last_error = None
            return entries
        except Exception as exc:
            self._handle_error("session_history_for_day", exc)
            return []

    def history_day_summaries(self, limit_days: int = 60) -> list[dict[str, int | str]]:
        try:
            limit_days = max(1, int(limit_days))
            with self._connection() as db:
                rows = _rows(
                    db.execute(
                        """
                        SELECT
                            substr(ended_at, 1, 10) AS day,
                            SUM(CASE WHEN mode = 'pomodoro' THEN 1 ELSE 0 END) AS pomodoros,
                            SUM(CASE WHEN mode = 'break' THEN 1 ELSE 0 END) AS breaks,
                            SUM(cards) AS cards,
                            SUM(xp) AS xp,
                            SUM(duration_seconds) AS duration_seconds
                        FROM sessions
                        WHERE ended_at != ''
                        GROUP BY day
                        ORDER BY day DESC
                        LIMIT ?
                        """,
                        (limit_days,),
                    )
                )
            self.last_error = None
            return [
                {
                    "day": str(row.get("day") or ""),
                    "pomodoros": _int(row.get("pomodoros"), 0),
                    "breaks": _int(row.get("breaks"), 0),
                    "cards": _int(row.get("cards"), 0),
                    "xp": _int(row.get("xp"), 0),
                    "duration_seconds": _int(row.get("duration_seconds"), 0),
                }
                for row in rows
                if row.get("day")
            ]
        except Exception as exc:
            self._handle_error("history_day_summaries", exc)
            return []

    def record_review_event(
        self,
        *,
        answered_at: str,
        session_id: str,
        card_id: int,
        ease: int,
        card_kind: str,
        deck_id: Optional[int],
        deck_name: str,
        xp: int,
    ) -> None:
        try:
            with self._connection() as db:
                db.execute(
                    """
                    INSERT INTO review_events (
                        answered_at, session_id, card_id, ease, card_kind, deck_id, deck_name, xp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (answered_at, session_id, int(card_id), int(ease), card_kind, deck_id, deck_name, int(xp)),
                )
            self.last_error = None
        except Exception as exc:
            self._handle_error("record_review_event", exc)

    def upsert_daily_stats(self, day: str, stats: dict) -> None:
        try:
            with self._connection() as db:
                self._upsert_daily_stats(db, day, stats)
            self.last_error = None
        except Exception as exc:
            self._handle_error("upsert_daily_stats", exc)

    def export_data(self) -> dict[str, list[dict[str, Any]]]:
        try:
            with self._connection() as db:
                data = {
                    "sessions": _rows(db.execute("SELECT * FROM sessions ORDER BY ended_at, id")),
                    "review_events": _rows(db.execute("SELECT * FROM review_events ORDER BY id")),
                    "daily_stats": _rows(db.execute("SELECT * FROM daily_stats ORDER BY day")),
                    "session_progress": _rows(db.execute("SELECT * FROM session_progress ORDER BY started_at, session_id")),
                }
            self.last_error = None
            return data
        except Exception as exc:
            self._handle_error("export", exc)
            return {"sessions": [], "review_events": [], "daily_stats": [], "session_progress": []}

    def replace_data(self, data: object) -> None:
        payload = data if isinstance(data, dict) else {}
        try:
            with self._connection() as db:
                db.execute("DELETE FROM review_events")
                db.execute("DELETE FROM sessions")
                db.execute("DELETE FROM daily_stats")
                db.execute("DELETE FROM session_progress")
                db.execute("DELETE FROM app_meta WHERE key != ?", ("schema_version",))
                for row in _safe_rows(payload.get("sessions")):
                    db.execute(
                        """
                        INSERT OR REPLACE INTO sessions (
                            id, mode, session_index, session_total, started_at, ended_at,
                            duration_seconds, cards, xp, retention, completed, deck_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(row.get("id") or uuid4().hex),
                            str(row.get("mode") or "pomodoro"),
                            _int(row.get("session_index"), 1),
                            _int(row.get("session_total"), 4),
                            str(row.get("started_at") or ""),
                            str(row.get("ended_at") or ""),
                            _int(row.get("duration_seconds"), 0),
                            _int(row.get("cards"), 0),
                            _int(row.get("xp"), 0),
                            _int(row.get("retention"), 0),
                            1 if row.get("completed") else 0,
                            str(row.get("deck_name") or ""),
                        ),
                    )
                for row in _safe_rows(payload.get("review_events")):
                    db.execute(
                        """
                        INSERT INTO review_events (
                            id, answered_at, session_id, card_id, ease, card_kind, deck_id, deck_name, xp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row.get("id"),
                            str(row.get("answered_at") or ""),
                            str(row.get("session_id") or ""),
                            _int(row.get("card_id"), 0),
                            _int(row.get("ease"), 0),
                            str(row.get("card_kind") or ""),
                            _optional_int(row.get("deck_id")),
                            str(row.get("deck_name") or ""),
                            _int(row.get("xp"), 0),
                        ),
                    )
                for row in _safe_rows(payload.get("daily_stats")):
                    self._upsert_daily_stats(db, str(row.get("day") or ""), row)
                for row in _safe_rows(payload.get("session_progress")):
                    self._insert_session_progress_row(db, row)
                if any(_safe_rows(payload.get(key)) for key in ("sessions", "review_events", "daily_stats", "session_progress")):
                    self._set_meta(db, JSON_MIGRATION_KEY, "done")
            self.last_error = None
        except Exception as exc:
            self._handle_error("replace", exc)

    def _ensure_schema(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self._connection() as db:
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS app_meta (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        mode TEXT NOT NULL,
                        session_index INTEGER NOT NULL,
                        session_total INTEGER NOT NULL,
                        started_at TEXT NOT NULL,
                        ended_at TEXT NOT NULL,
                        duration_seconds INTEGER NOT NULL,
                        cards INTEGER NOT NULL,
                        xp INTEGER NOT NULL,
                        retention INTEGER NOT NULL,
                        completed INTEGER NOT NULL,
                        deck_name TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_sessions_ended_at ON sessions(ended_at);
                    CREATE INDEX IF NOT EXISTS idx_sessions_mode ON sessions(mode);
                    CREATE TABLE IF NOT EXISTS review_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        answered_at TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        card_id INTEGER NOT NULL,
                        ease INTEGER NOT NULL,
                        card_kind TEXT NOT NULL,
                        deck_id INTEGER,
                        deck_name TEXT NOT NULL,
                        xp INTEGER NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_review_events_answered_at ON review_events(answered_at);
                    CREATE INDEX IF NOT EXISTS idx_review_events_session_id ON review_events(session_id);
                    CREATE INDEX IF NOT EXISTS idx_review_events_deck_id ON review_events(deck_id);
                    CREATE TABLE IF NOT EXISTS daily_stats (
                        day TEXT PRIMARY KEY,
                        cards INTEGER NOT NULL,
                        xp INTEGER NOT NULL,
                        again INTEGER NOT NULL,
                        hard INTEGER NOT NULL,
                        good INTEGER NOT NULL,
                        easy INTEGER NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS session_progress (
                        session_id TEXT PRIMARY KEY,
                        started_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        session_index INTEGER NOT NULL,
                        session_total INTEGER NOT NULL,
                        cards INTEGER NOT NULL,
                        new_cards INTEGER NOT NULL,
                        review_cards INTEGER NOT NULL,
                        again_cards INTEGER NOT NULL,
                        hard_cards INTEGER NOT NULL,
                        good_cards INTEGER NOT NULL,
                        easy_cards INTEGER NOT NULL,
                        xp INTEGER NOT NULL,
                        deck_id INTEGER,
                        deck_name TEXT NOT NULL
                    );
                    """
                )
                self._set_meta(db, "schema_version", str(SCHEMA_VERSION))
            self.last_error = None
        except Exception as exc:
            self._handle_error("schema", exc)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.path))
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    @contextmanager
    def _connection(self):
        db = self._connect()
        try:
            with db:
                yield db
        finally:
            db.close()

    def _insert_session(self, db: sqlite3.Connection, session_id: str, entry: SessionHistoryEntry) -> None:
        db.execute(
            """
            INSERT OR REPLACE INTO sessions (
                id, mode, session_index, session_total, started_at, ended_at,
                duration_seconds, cards, xp, retention, completed, deck_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                entry.mode,
                entry.session_index,
                entry.session_total,
                entry.started_at,
                entry.ended_at,
                entry.duration_seconds,
                entry.cards,
                entry.xp,
                entry.retention,
                1 if entry.completed else 0,
                entry.deck_name,
            ),
        )

    def _ensure_session_progress(self, db: sqlite3.Connection, session: StudySessionState) -> None:
        if not session.id:
            return
        row = db.execute("SELECT session_id FROM session_progress WHERE session_id = ?", (session.id,)).fetchone()
        if row is not None:
            db.execute(
                """
                UPDATE session_progress
                SET session_index = ?, session_total = ?, deck_id = COALESCE(?, deck_id),
                    deck_name = CASE WHEN ? != '' THEN ? ELSE deck_name END
                WHERE session_id = ?
                """,
                (session.session_index, session.session_total, session.deck_id, session.deck_name, session.deck_name, session.id),
            )
            return
        self._insert_session_progress_row(
            db,
            {
                "session_id": session.id,
                "started_at": session.started_at,
                "updated_at": session.updated_at or session.started_at,
                "session_index": session.session_index,
                "session_total": session.session_total,
                "cards": 0,
                "new_cards": 0,
                "review_cards": 0,
                "again_cards": 0,
                "hard_cards": 0,
                "good_cards": 0,
                "easy_cards": 0,
                "xp": 0,
                "deck_id": session.deck_id,
                "deck_name": session.deck_name,
            },
        )

    def _seed_session_progress(self, db: sqlite3.Connection, session: StudySessionState) -> None:
        if not session.id:
            return
        row = db.execute("SELECT session_id FROM session_progress WHERE session_id = ?", (session.id,)).fetchone()
        if row is not None:
            return
        self._insert_session_progress_row(
            db,
            {
                "session_id": session.id,
                "started_at": session.started_at,
                "updated_at": session.updated_at or session.started_at,
                "session_index": session.session_index,
                "session_total": session.session_total,
                "cards": session.cards,
                "new_cards": session.new_cards,
                "review_cards": session.review_cards,
                "again_cards": session.again_cards,
                "hard_cards": session.hard_cards,
                "good_cards": session.good_cards,
                "easy_cards": session.easy_cards,
                "xp": session.xp_current,
                "deck_id": session.deck_id,
                "deck_name": session.deck_name,
            },
        )

    def _insert_session_progress_row(self, db: sqlite3.Connection, row: dict[str, Any]) -> None:
        session_id = str(row.get("session_id") or row.get("id") or "")
        if not session_id:
            return
        db.execute(
            """
            INSERT OR REPLACE INTO session_progress (
                session_id, started_at, updated_at, session_index, session_total,
                cards, new_cards, review_cards, again_cards, hard_cards, good_cards,
                easy_cards, xp, deck_id, deck_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                str(row.get("started_at") or ""),
                str(row.get("updated_at") or row.get("started_at") or ""),
                _int(row.get("session_index"), 1),
                _int(row.get("session_total"), 4),
                _int(row.get("cards"), 0),
                _int(row.get("new_cards"), 0),
                _int(row.get("review_cards"), 0),
                _int(row.get("again_cards"), 0),
                _int(row.get("hard_cards"), 0),
                _int(row.get("good_cards"), 0),
                _int(row.get("easy_cards"), 0),
                _int(row.get("xp"), 0),
                _optional_int(row.get("deck_id")),
                str(row.get("deck_name") or ""),
            ),
        )

    def _upsert_daily_stats(self, db: sqlite3.Connection, day: str, stats: dict) -> None:
        if not day:
            return
        db.execute(
            """
            INSERT OR REPLACE INTO daily_stats (day, cards, xp, again, hard, good, easy)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                day,
                _int(stats.get("cards"), 0),
                _int(stats.get("xp"), 0),
                _int(stats.get("again"), 0),
                _int(stats.get("hard"), 0),
                _int(stats.get("good"), 0),
                _int(stats.get("easy"), 0),
            ),
        )

    def _increment_daily_stats(self, db: sqlite3.Connection, day: str, ease: int, xp: int) -> None:
        if not day:
            return
        db.execute(
            """
            INSERT INTO daily_stats (day, cards, xp, again, hard, good, easy)
            VALUES (?, 1, MAX(0, ?), ?, ?, ?, ?)
            ON CONFLICT(day) DO UPDATE SET
                cards = daily_stats.cards + 1,
                xp = MAX(0, daily_stats.xp + ?),
                again = daily_stats.again + excluded.again,
                hard = daily_stats.hard + excluded.hard,
                good = daily_stats.good + excluded.good,
                easy = daily_stats.easy + excluded.easy
            """,
            (
                day,
                xp,
                1 if ease == 1 else 0,
                1 if ease == 2 else 0,
                1 if ease == 3 else 0,
                1 if ease == 4 else 0,
                xp,
            ),
        )

    def _daily_stats_row(self, db: sqlite3.Connection, day: str) -> dict[str, Any]:
        row = db.execute("SELECT cards, xp, again, hard, good, easy FROM daily_stats WHERE day = ?", (day,)).fetchone()
        return dict(row) if row is not None else {"cards": 0, "xp": 0, "again": 0, "hard": 0, "good": 0, "easy": 0}

    def _daily_review_progress_row(self, db: sqlite3.Connection, day: str) -> dict[str, Any]:
        row = db.execute(
            """
            SELECT
                COUNT(*) AS cards,
                SUM(CASE WHEN card_kind = 'new' THEN 1 ELSE 0 END) AS new_cards,
                SUM(CASE WHEN card_kind = 'new' THEN 0 ELSE 1 END) AS review_cards,
                SUM(CASE WHEN ease = 1 THEN 1 ELSE 0 END) AS again_cards,
                SUM(CASE WHEN ease = 2 THEN 1 ELSE 0 END) AS hard_cards,
                SUM(CASE WHEN ease = 3 THEN 1 ELSE 0 END) AS good_cards,
                SUM(CASE WHEN ease = 4 THEN 1 ELSE 0 END) AS easy_cards,
                SUM(xp) AS xp
            FROM review_events
            WHERE substr(answered_at, 1, 10) = ?
            """,
            (day,),
        ).fetchone()
        progress = dict(row) if row is not None else _empty_progress()
        if _int(progress.get("cards"), 0) > 0:
            return progress

        stats = self._daily_stats_row(db, day)
        return {
            "cards": _int(stats.get("cards"), 0),
            "new_cards": 0,
            "review_cards": _int(stats.get("cards"), 0),
            "again_cards": _int(stats.get("again"), 0),
            "hard_cards": _int(stats.get("hard"), 0),
            "good_cards": _int(stats.get("good"), 0),
            "easy_cards": _int(stats.get("easy"), 0),
            "xp": _int(stats.get("xp"), 0),
        }

    def _session_progress_row(self, db: sqlite3.Connection, session: StudySessionState) -> dict[str, Any]:
        if not session.id:
            return _progress_from_session(session)
        self._ensure_session_progress(db, session)
        row = db.execute("SELECT * FROM session_progress WHERE session_id = ?", (session.id,)).fetchone()
        return dict(row) if row is not None else _progress_from_session(session)

    def _meta(self, key: str) -> str:
        try:
            with self._connection() as db:
                row = db.execute("SELECT value FROM app_meta WHERE key = ?", (key,)).fetchone()
            return str(row["value"]) if row else ""
        except Exception as exc:
            self._handle_error("meta", exc)
            return ""

    def _set_meta(self, db: sqlite3.Connection, key: str, value: str) -> None:
        db.execute("INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)", (key, value))

    def _handle_error(self, action: str, exc: Exception) -> None:
        self.last_error = exc
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            log_path = self.path.with_name("pomodoro_qt.log")
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"{timestamp} analytics.{action}: {type(exc).__name__}: {exc}\n")
        except Exception:
            pass

    def _resolve_path(self) -> Path:
        profile_folder = None
        try:
            pm = getattr(self._mw, "pm", None)
            profile_folder_fn = getattr(pm, "profileFolder", None)
            if callable(profile_folder_fn):
                profile_folder = profile_folder_fn()
        except Exception:
            profile_folder = None

        if profile_folder:
            return Path(profile_folder) / DB_FILENAME

        try:
            addon_folder = self._mw.addonManager.addonsFolder(self._addon_package)
            return Path(addon_folder) / DB_FILENAME
        except Exception:
            return Path(__file__).resolve().parent.parent / DB_FILENAME


def _rows(cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor.fetchall()]


def _safe_rows(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _int(value: object, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _optional_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
            return None


def _migration_session_id(index: int, entry: SessionHistoryEntry) -> str:
    payload = json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True)
    return f"json-history-{index}-{sha1(payload.encode('utf-8')).hexdigest()}"


def _progress_from_session(session: StudySessionState) -> dict[str, Any]:
    return {
        "session_id": session.id,
        "started_at": session.started_at,
        "updated_at": session.updated_at,
        "session_index": session.session_index,
        "session_total": session.session_total,
        "cards": session.cards,
        "new_cards": session.new_cards,
        "learning_cards": session.new_cards,
        "review_cards": session.review_cards,
        "relearning_cards": 0,
        "filtered_cards": 0,
        "again_cards": session.again_cards,
        "hard_cards": session.hard_cards,
        "good_cards": session.good_cards,
        "easy_cards": session.easy_cards,
        "xp": session.xp_current,
        "deck_id": session.deck_id,
        "deck_name": session.deck_name,
    }


def _empty_progress() -> dict[str, int]:
    return {
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
    }


def _progress_from_sequence(row: object) -> dict[str, int]:
    values = list(row) if row is not None else []
    keys = [
        "cards",
        "learning_cards",
        "review_cards",
        "relearning_cards",
        "filtered_cards",
        "again_cards",
        "hard_cards",
        "good_cards",
        "easy_cards",
    ]
    progress = _empty_progress()
    for index, key in enumerate(keys):
        progress[key] = _int(values[index], 0) if index < len(values) else 0
    progress["new_cards"] = progress["learning_cards"]
    return progress


def _xp_from_progress(progress: dict[str, Any]) -> int:
    xp = (
        _int(progress.get("hard_cards"), 0)
        + _int(progress.get("good_cards"), 0) * 2
        + _int(progress.get("easy_cards"), 0)
        - _int(progress.get("again_cards"), 0)
    )
    return max(0, xp)


def _empty_anki_review_streaks() -> dict[str, Any]:
    return {
        "streak_days": 0,
        "longest_streak_days": 0,
        "streak_start_date": "",
        "today_cards": 0,
        "today_xp": 0,
        "today_reviews": 0,
        "yesterday_reviews": 0,
        "cutoff_hour": 4,
        "seconds_until_cutoff": 0,
    }


def _anki_rollover_seconds(col: Any) -> int:
    conf = getattr(col, "conf", None)
    if isinstance(conf, dict):
        try:
            rollover_hour = int(conf.get("rollover"))
            return max(0, min(23, rollover_hour)) * 3600
        except (TypeError, ValueError):
            pass
    cutoff = _anki_day_cutoff(col)
    if cutoff is None:
        return 4 * 3600
    try:
        rollover = datetime.fromtimestamp(int(cutoff))
    except (OSError, OverflowError, TypeError, ValueError):
        return 4 * 3600
    return max(0, min(23 * 3600 + 59 * 60, rollover.hour * 3600 + rollover.minute * 60))


def _anki_today_start(db: Any, rollover_seconds: int) -> int:
    if int(rollover_seconds) % 3600 == 0:
        modifier = f"-{int(rollover_seconds) // 3600} hours"
    else:
        modifier = f"-{max(0, int(rollover_seconds))} seconds"
    try:
        value = db.scalar(
            "SELECT CAST(STRFTIME('%s', 'now', ?, 'localtime', 'start of day') AS int)",
            modifier,
        )
        return int(value)
    except Exception:
        return int(datetime.now().timestamp())


def _anki_day_cutoff(col: Any) -> Optional[int]:
    sched = getattr(col, "sched", None)
    for name in ("day_cutoff", "dayCutoff"):
        value = getattr(sched, name, None)
        if callable(value):
            try:
                value = value()
            except Exception:
                continue
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _day_key(day_start: int) -> str:
    return datetime.fromtimestamp(day_start).date().isoformat()


def _entry_from_progress(
    session: StudySessionState,
    progress: dict[str, Any],
    mode: str,
    ended_at: str,
    duration_seconds: int,
    completed: bool,
) -> SessionHistoryEntry:
    cards = _int(progress.get("cards"), 0)
    again_cards = _int(progress.get("again_cards"), 0)
    retention = round((cards - again_cards) * 100 / cards) if cards > 0 else 0
    return SessionHistoryEntry(
        mode=MODE_BREAK if mode == MODE_BREAK else MODE_POMODORO,
        session_index=_int(progress.get("session_index"), session.session_index),
        session_total=_int(progress.get("session_total"), session.session_total),
        started_at=str(progress.get("started_at") or session.started_at),
        ended_at=ended_at,
        duration_seconds=max(0, int(duration_seconds)),
        cards=cards,
        xp=_int(progress.get("xp"), 0),
        retention=retention,
        completed=completed,
        deck_name=str(progress.get("deck_name") or session.deck_name),
    )


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


def _seconds_until_cutoff(today_start: int, rollover_seconds: int) -> int:
    next_cutoff = int(today_start) + 86400 + max(0, int(rollover_seconds))
    now = int(datetime.now().timestamp())
    while next_cutoff <= now:
        next_cutoff += 86400
    return max(0, next_cutoff - now)


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
