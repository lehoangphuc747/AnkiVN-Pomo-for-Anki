from __future__ import annotations

import unittest

from pomodoro_qt.audio_volume import clamp_local_volume_percent, local_volume_fraction, local_volume_label


class AudioVolumeTests(unittest.TestCase):
    def test_clamp_local_volume_percent(self) -> None:
        self.assertEqual(clamp_local_volume_percent(None), 65)
        self.assertEqual(clamp_local_volume_percent("bad"), 65)
        self.assertEqual(clamp_local_volume_percent(-1), 0)
        self.assertEqual(clamp_local_volume_percent(101), 100)
        self.assertEqual(clamp_local_volume_percent("42"), 42)

    def test_local_volume_fraction_uses_qt_scale(self) -> None:
        self.assertEqual(local_volume_fraction(-1), 0.0)
        self.assertEqual(local_volume_fraction(100), 1.0)
        self.assertEqual(local_volume_fraction(65), 0.65)

    def test_local_volume_label(self) -> None:
        self.assertEqual(local_volume_label("42"), "42%")


if __name__ == "__main__":
    unittest.main()
