from __future__ import annotations

import unittest
from datetime import datetime

from pomodoro_vn.pomodoro_qt.models import MODE_BREAK, MODE_POMODORO, SessionHistoryEntry, SessionMetrics
from pomodoro_vn.pomodoro_qt.session_manager import PomodoroSessionManager


class DummyStore:
    def __init__(self, state: dict | None = None) -> None:
        self.state = state or {}

    def load(self) -> dict:
        return dict(self.state)

    def save(self, data: dict) -> bool:
        self.state = dict(data)
        return True


class DummyAnalyticsStore:
    def __init__(self, today_entries: list[SessionHistoryEntry] | None = None) -> None:
        self._today_entries = today_entries or []

    def bootstrap_from_json(self, history, daily_stats, active_session) -> None:
        pass

    def session_history_for_day(self, day: str) -> list[SessionHistoryEntry]:
        return list(self._today_entries)

    def history_day_summaries(self, limit_days: int = 60) -> list[dict]:
        return []

    def metrics_source(self, session) -> dict:
        return {"progress": {}, "total_xp": 0}


class FocusTimeMetricTests(unittest.TestCase):
    def test_today_focus_seconds_sums_pomodoros_only(self) -> None:
        now_iso = datetime.now().isoformat()
        entries = [
            SessionHistoryEntry(mode=MODE_POMODORO, duration_seconds=1500, ended_at=now_iso, completed=True),
            SessionHistoryEntry(mode=MODE_BREAK, duration_seconds=300, ended_at=now_iso, completed=True),
            SessionHistoryEntry(mode=MODE_POMODORO, duration_seconds=1200, ended_at=now_iso, completed=True),
        ]
        store = DummyStore()
        analytics = DummyAnalyticsStore(today_entries=entries)
        manager = PomodoroSessionManager(store=store, analytics_store=analytics)  # type: ignore[arg-type]

        self.assertEqual(manager.today_focus_seconds(), 2700)
        metrics = manager.metrics()
        self.assertEqual(metrics.today_focus_seconds, 2700)


if __name__ == "__main__":
    unittest.main()
