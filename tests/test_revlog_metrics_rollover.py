from __future__ import annotations

import sqlite3
import unittest
from unittest.mock import patch

from pomodoro_qt.revlog_metrics import RevlogMetricsSource


DAY = 86400
TODAY = 1704067200


class _Db:
    def __init__(self) -> None:
        self._conn = sqlite3.connect(":memory:")
        self._conn.execute(
            "CREATE TABLE revlog (id INTEGER NOT NULL, cid INTEGER, ease INTEGER NOT NULL, type INTEGER NOT NULL, time INTEGER NOT NULL)"
        )

    def add_review(
        self,
        timestamp_seconds: int,
        ease: int = 3,
        card_type: int = 1,
        cid: int | None = None,
        time_ms: int = 0,
    ) -> None:
        self._conn.execute(
            "INSERT INTO revlog (id, cid, ease, type, time) VALUES (?, ?, ?, ?, ?)",
            (
                int(timestamp_seconds) * 1000,
                int(cid if cid is not None else timestamp_seconds),
                int(ease),
                int(card_type),
                int(time_ms),
            ),
        )
        self._conn.commit()

    def first(self, sql: str, *args):
        return self._conn.execute(sql, args).fetchone()

    def all(self, sql: str, *args):
        return self._conn.execute(sql, args).fetchall()

    def scalar(self, sql: str, *args):
        row = self.first(sql, *args)
        return row[0] if row else None


class _Col:
    def __init__(self, db: _Db) -> None:
        self.db = db
        self.conf = {"rollover": 0}


class _Mw:
    def __init__(self, db: _Db) -> None:
        self.col = _Col(db)


class RevlogMetricsRolloverTests(unittest.TestCase):
    def test_metrics_recompute_when_anki_day_changes_without_new_answer(self) -> None:
        db = _Db()
        db.add_review(TODAY + 60)
        source = RevlogMetricsSource(_Mw(db))

        with patch("pomodoro_qt.revlog_metrics.anki_rollover_seconds", return_value=0):
            with patch("pomodoro_qt.revlog_metrics.anki_today_start", return_value=TODAY):
                old_day = source.metrics()
            with patch("pomodoro_qt.revlog_metrics.anki_today_start", return_value=TODAY + DAY):
                new_day = source.metrics()

        self.assertEqual(old_day.cards.cards, 1)
        self.assertEqual(old_day.retention.today_cards, 1)
        self.assertEqual(new_day.cards.cards, 0)
        self.assertEqual(new_day.retention.today_cards, 0)

    def test_today_window_uses_anki_today_start_without_extra_rollover(self) -> None:
        db = _Db()
        db.add_review(TODAY + 60 * 60)
        source = RevlogMetricsSource(_Mw(db))

        with patch("pomodoro_qt.revlog_metrics.anki_rollover_seconds", return_value=4 * 60 * 60):
            with patch("pomodoro_qt.revlog_metrics.anki_today_start", return_value=TODAY):
                snapshot = source.metrics()

        self.assertEqual(snapshot.cards.cards, 1)
        self.assertEqual(snapshot.retention.today_cards, 1)

    def test_experience_counts_repeated_card_once_on_same_anki_day(self) -> None:
        db = _Db()
        db.add_review(TODAY + 60, ease=1, cid=123)
        db.add_review(TODAY + 120, ease=3, cid=123)
        db.add_review(TODAY + 180, ease=4, cid=456)
        source = RevlogMetricsSource(_Mw(db))

        with patch("pomodoro_qt.revlog_metrics.anki_rollover_seconds", return_value=0):
            with patch("pomodoro_qt.revlog_metrics.anki_today_start", return_value=TODAY):
                snapshot = source.metrics()

        self.assertEqual(snapshot.cards.cards, 3)
        self.assertEqual(snapshot.experience.unique_cards, 2)
        self.assertEqual(snapshot.experience.experience, 2)
        self.assertEqual(snapshot.experience.again_cards, 1)
        self.assertEqual(snapshot.experience.good_cards, 1)
        self.assertEqual(snapshot.experience.easy_cards, 1)

    def test_experience_counts_same_card_again_on_another_anki_day_in_streak(self) -> None:
        db = _Db()
        db.add_review(TODAY + 60, ease=3, cid=123)
        db.add_review(TODAY + DAY + 60, ease=1, cid=123)
        source = RevlogMetricsSource(_Mw(db))

        with patch("pomodoro_qt.revlog_metrics.anki_rollover_seconds", return_value=0):
            with patch("pomodoro_qt.revlog_metrics.anki_today_start", return_value=TODAY + DAY):
                snapshot = source.metrics()

        self.assertEqual(snapshot.streak.days, 2)
        self.assertEqual(snapshot.experience.unique_cards, 2)
        self.assertEqual(snapshot.experience.experience, 2)
        self.assertEqual(snapshot.experience.again_cards, 1)
        self.assertEqual(snapshot.experience.good_cards, 1)

    def test_invalidate_today_snapshot_refreshes_cached_stale_answer(self) -> None:
        db = _Db()
        db.add_review(TODAY + 60, ease=3, cid=123)
        source = RevlogMetricsSource(_Mw(db))

        with patch("pomodoro_qt.revlog_metrics.anki_rollover_seconds", return_value=0):
            with patch("pomodoro_qt.revlog_metrics.anki_today_start", return_value=TODAY):
                initial = source.metrics()
                self.assertEqual(initial.cards.cards, 1)

                source.note_review_answered(1)
                stale = source.metrics()
                self.assertEqual(stale.cards.cards, 1)
                self.assertEqual(stale.retention.today_retention, 100)

                db.add_review(TODAY + 120, ease=1, cid=456)
                cached = source.metrics()
                self.assertEqual(cached.cards.cards, 1)
                self.assertEqual(cached.retention.today_retention, 100)

                source.invalidate_today_snapshot()
                refreshed = source.metrics()

        self.assertEqual(refreshed.cards.cards, 2)
        self.assertEqual(refreshed.retention.today_retention, 50)
        self.assertEqual(refreshed.retention.today_cards, 2)

    def test_study_time_uses_revlog_time_in_anki_today_window(self) -> None:
        db = _Db()
        db.add_review(TODAY - 60, ease=3, cid=1, time_ms=60_000)
        db.add_review(TODAY + 60, ease=3, cid=2, time_ms=61_000)
        db.add_review(TODAY + 120, ease=1, cid=3, time_ms=59_000)
        db.add_review(TODAY + 180, ease=0, cid=4, time_ms=30_000)
        source = RevlogMetricsSource(_Mw(db))

        with patch("pomodoro_qt.revlog_metrics.anki_rollover_seconds", return_value=0):
            with patch("pomodoro_qt.revlog_metrics.anki_today_start", return_value=TODAY):
                snapshot = source.metrics()

        self.assertEqual(snapshot.study_time.today_seconds, 120)
        self.assertEqual(snapshot.study_time.all_time_seconds, 180)
        self.assertEqual(snapshot.study_time.today_reviews, 2)
        self.assertEqual(snapshot.study_time.all_time_reviews, 3)

    def test_metrics_cache_isolated_by_collection_identity(self) -> None:
        first_db = _Db()
        first_db.add_review(TODAY + 60, ease=3, cid=1)
        second_db = _Db()
        second_db.add_review(TODAY + 60, ease=1, cid=2)
        second_db.add_review(TODAY + 120, ease=3, cid=3)
        mw = _Mw(first_db)
        source = RevlogMetricsSource(mw)

        with patch("pomodoro_qt.revlog_metrics.anki_rollover_seconds", return_value=0):
            with patch("pomodoro_qt.revlog_metrics.anki_today_start", return_value=TODAY):
                first = source.metrics()
                mw.col = _Col(second_db)
                second = source.metrics()

        self.assertEqual(first.cards.cards, 1)
        self.assertEqual(first.retention.today_retention, 100)
        self.assertEqual(second.cards.cards, 2)
        self.assertEqual(second.retention.today_retention, 50)


if __name__ == "__main__":
    unittest.main()
