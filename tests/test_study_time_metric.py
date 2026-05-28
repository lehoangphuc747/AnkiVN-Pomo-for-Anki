from __future__ import annotations

import unittest

from pomodoro_qt.i18n import set_language
from pomodoro_qt.study_time_metric import format_study_duration, format_study_duration_long


class StudyTimeMetricTests(unittest.TestCase):
    def test_format_study_duration_uses_compact_hours_minutes(self) -> None:
        self.assertEqual(format_study_duration(0), "0m")
        self.assertEqual(format_study_duration(45 * 60), "45m")
        self.assertEqual(format_study_duration(2 * 3600 + 5 * 60), "2h 05m")

    def test_format_study_duration_long_uses_full_units(self) -> None:
        self.addCleanup(set_language, "vi")
        minute = 60
        hour = 60 * minute

        set_language("vi")
        self.assertEqual(format_study_duration_long(0), "0 giờ 00 phút")
        self.assertEqual(format_study_duration_long(65 * minute), "1 giờ 05 phút")
        self.assertEqual(format_study_duration_long(123 * hour + 5 * minute), "123 giờ 05 phút")

        set_language("en")
        self.assertEqual(format_study_duration_long(0), "0h 00m")
        self.assertEqual(format_study_duration_long(65 * minute), "1h 05m")
        self.assertEqual(format_study_duration_long(123 * hour + 5 * minute), "123h 05m")


if __name__ == "__main__":
    unittest.main()
