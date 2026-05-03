from __future__ import annotations

import unittest

from pomodoro_qt.i18n import format_number, set_language


class NumberFormatTests(unittest.TestCase):
    def tearDown(self) -> None:
        set_language("vi")

    def test_english_uses_comma_thousands(self) -> None:
        set_language("en")

        self.assertEqual(format_number(999), "999")
        self.assertEqual(format_number(1000), "1,000")
        self.assertEqual(format_number(1234567), "1,234,567")

    def test_vietnamese_uses_dot_thousands(self) -> None:
        set_language("vi")

        self.assertEqual(format_number(999), "999")
        self.assertEqual(format_number(1000), "1.000")
        self.assertEqual(format_number(1234567), "1.234.567")


if __name__ == "__main__":
    unittest.main()
