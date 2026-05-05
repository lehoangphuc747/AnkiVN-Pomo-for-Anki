from __future__ import annotations

import unittest
import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from pomodoro_qt.analytics_store import PomodoroAnalyticsStore
from pomodoro_qt.experience_metric import (
    XP_PER_ANKI_REVIEW_EVENT,
    XP_PER_UNIQUE_CARD,
    answer_experience,
    unique_cards_experience,
)
from pomodoro_qt.session_manager import PomodoroSessionManager
from pomodoro_qt.storage import PomodoroDataStore
from pomodoro_qt.tracking import CARD_KIND_REVIEW, ReviewAnswerEvent


class _FakeProfileManager:
    def __init__(self, profile_folder: Path) -> None:
        self._profile_folder = profile_folder

    def profileFolder(self) -> str:  # noqa: N802 - mirrors Anki API
        return str(self._profile_folder)


class _FakeMw:
    def __init__(self, profile_folder: Path) -> None:
        self.pm = _FakeProfileManager(profile_folder)


class GradeNeutralXpTests(unittest.TestCase):
    def test_answer_experience_does_not_add_storage_xp(self) -> None:
        values = [answer_experience(ease) for ease in (1, 2, 3, 4, None, 99)]

        self.assertEqual(values, [XP_PER_ANKI_REVIEW_EVENT] * len(values))

    def test_unique_cards_experience_uses_integer_unique_cards(self) -> None:
        self.assertEqual(unique_cards_experience(0), 0)
        self.assertEqual(unique_cards_experience(5), 5 * XP_PER_UNIQUE_CARD)
        self.assertEqual(unique_cards_experience(-10), 0)
        self.assertEqual(unique_cards_experience("bad"), 0)

    def test_review_grades_do_not_add_storage_xp_and_keep_grade_stats(self) -> None:
        with _profile_dir() as temp_dir:
            manager, analytics = _manager(Path(temp_dir))

            for ease in (1, 2, 3, 4):
                metrics = manager.record_answer(_event(ease))

            self.assertEqual(metrics.session_xp, 0)
            self.assertEqual(metrics.total_xp, 0)

            data = analytics.export_data()
            progress = data["session_progress"][0]
            self.assertEqual(progress["cards"], 4)
            self.assertEqual(progress["xp"], 0)
            self.assertEqual(progress["again_cards"], 1)
            self.assertEqual(progress["hard_cards"], 1)
            self.assertEqual(progress["good_cards"], 1)
            self.assertEqual(progress["easy_cards"], 1)
            self.assertEqual([row["xp"] for row in data["review_events"]], [0, 0, 0, 0])

            daily = data["daily_stats"][0]
            self.assertEqual(daily["cards"], 4)
            self.assertEqual(daily["xp"], 0)
            self.assertEqual((daily["again"], daily["hard"], daily["good"], daily["easy"]), (1, 1, 1, 1))

    def test_completed_pomodoro_does_not_add_xp(self) -> None:
        with _profile_dir() as temp_dir:
            manager, analytics = _manager(Path(temp_dir))
            for ease in (1, 3):
                manager.record_answer(_event(ease))

            completed = manager.complete_pomodoro(duration_seconds=25 * 60)

            self.assertEqual(completed.session_xp, 0)
            self.assertEqual(completed.total_xp, 0)

            data = analytics.export_data()
            self.assertEqual(len(data["review_events"]), 2)
            self.assertEqual(data["sessions"][0]["xp"], 0)
            self.assertEqual(data["sessions"][0]["completed"], 1)

            daily = data["daily_stats"][0]
            self.assertEqual(daily["cards"], 2)
            self.assertEqual(daily["xp"], 0)
            self.assertEqual((daily["again"], daily["hard"], daily["good"], daily["easy"]), (1, 0, 1, 0))

    def test_stopped_session_does_not_receive_pomodoro_bonus(self) -> None:
        with _profile_dir() as temp_dir:
            manager, analytics = _manager(Path(temp_dir))
            manager.record_answer(_event(1))

            manager.stop_current_session("pomodoro", duration_seconds=60)

            data = analytics.export_data()
            self.assertEqual(data["sessions"][0]["xp"], 0)
            self.assertEqual(data["sessions"][0]["completed"], 0)
            self.assertEqual(data["daily_stats"][0]["xp"], 0)


def _manager(profile_folder: Path) -> tuple[PomodoroSessionManager, PomodoroAnalyticsStore]:
    mw = _FakeMw(profile_folder)
    analytics = PomodoroAnalyticsStore(mw, "Pomodoro")
    store = PomodoroDataStore(mw, "Pomodoro")
    return PomodoroSessionManager(store, analytics), analytics


@contextmanager
def _profile_dir():
    base = Path.cwd() / "test_tmp"
    base.mkdir(exist_ok=True)
    path = base / uuid4().hex
    path.mkdir()
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _event(ease: int) -> ReviewAnswerEvent:
    return ReviewAnswerEvent(
        card_id=1000 + ease,
        ease=ease,
        card_kind=CARD_KIND_REVIEW,
        deck_id=1,
        deck_name="Default",
    )


if __name__ == "__main__":
    unittest.main()
