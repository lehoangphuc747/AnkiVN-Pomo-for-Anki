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
            "CREATE TABLE revlog (id INTEGER NOT NULL, cid INTEGER, ease INTEGER NOT NULL, type INTEGER NOT NULL)"
        )

    def add_review(self, timestamp_seconds: int, ease: int = 3, card_type: int = 1) -> None:
        self._conn.execute(
            "INSERT INTO revlog (id, cid, ease, type) VALUES (?, ?, ?, ?)",
            (int(timestamp_seconds) * 1000, int(timestamp_seconds), int(ease), int(card_type)),
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

    def test_metrics_recompute_when_rollover_changes_for_same_anki_day(self) -> None:
        db = _Db()
        db.add_review(TODAY + 60 * 60)
        source = RevlogMetricsSource(_Mw(db))

        with patch("pomodoro_qt.revlog_metrics.anki_today_start", return_value=TODAY):
            with patch("pomodoro_qt.revlog_metrics.anki_rollover_seconds", return_value=0):
                midnight_rollover = source.metrics()
            with patch("pomodoro_qt.revlog_metrics.anki_rollover_seconds", return_value=4 * 60 * 60):
                four_hour_rollover = source.metrics()

        self.assertEqual(midnight_rollover.cards.cards, 1)
        self.assertEqual(four_hour_rollover.cards.cards, 0)


if __name__ == "__main__":
    unittest.main()
