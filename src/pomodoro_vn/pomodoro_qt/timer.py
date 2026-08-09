"""Pomodoro timer state machine backed by Qt's event loop."""

from __future__ import annotations

import math
import time
from datetime import datetime
from typing import Optional

from aqt.qt import QObject, QTimer, pyqtSignal

from .models import MODE_BREAK, MODE_POMODORO, PomodoroSettings, PomodoroTimerState, TimerRuntimeState


class PomodoroTimer(QObject):
    changed = pyqtSignal(object)
    pomodoro_completed = pyqtSignal()
    break_completed = pyqtSignal()
    break_done = pyqtSignal()
    pomodoro_done = pyqtSignal()
    mode_started = pyqtSignal(str)

    def __init__(self, settings: PomodoroSettings) -> None:
        super().__init__()
        self.settings = settings
        self.mode = MODE_POMODORO
        self.total_seconds = self._seconds_for_mode(self.mode)
        self.time_left = self.total_seconds
        self.paused = True
        self._started = False
        self._deadline: Optional[float] = None
        self._is_overtime = False
        self._overtime_seconds = 0
        self._overtime_started_at: Optional[float] = None
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    @property
    def is_overtime(self) -> bool:
        return self._is_overtime

    @property
    def overtime_seconds(self) -> int:
        self._sync_overtime_seconds()
        return self._overtime_seconds

    def state(self) -> PomodoroTimerState:
        self._sync_running_time_left()
        self._sync_overtime_seconds()
        return PomodoroTimerState(
            mode=self.mode,
            total_seconds=self.total_seconds,
            time_left=self.time_left,
            paused=self.paused,
            started=self._started,
            is_overtime=self._is_overtime,
            overtime_seconds=self._overtime_seconds,
        )

    def runtime_state(self) -> TimerRuntimeState:
        self._sync_running_time_left()
        self._sync_overtime_seconds()
        return TimerRuntimeState(
            mode=self.mode,
            total_seconds=self.total_seconds,
            time_left=self.time_left,
            paused=self.paused,
            started=self._started,
            saved_at=datetime.now().astimezone().isoformat(timespec="seconds"),
            is_overtime=self._is_overtime,
            overtime_seconds=self._overtime_seconds,
        )

    def restore_state(self, state: TimerRuntimeState) -> None:
        self.mode = MODE_BREAK if state.mode == MODE_BREAK else MODE_POMODORO
        configured_total = self._seconds_for_mode(self.mode)
        self.total_seconds = configured_total
        self.time_left = max(0, min(configured_total, int(state.time_left)))
        self.paused = bool(state.paused)
        self._is_overtime = bool(state.is_overtime) and self.mode == MODE_POMODORO
        self._overtime_seconds = max(0, int(state.overtime_seconds)) if self._is_overtime else 0
        if self._is_overtime:
            self.time_left = 0
            self._started = True
            self._overtime_started_at = time.monotonic() - self._overtime_seconds if not self.paused else None
            self._deadline = None
        else:
            self._started = bool(state.started or not self.paused or self.time_left < self.total_seconds)
            self._deadline = self._make_deadline(self.time_left) if not self.paused and self.time_left > 0 else None
            self._overtime_started_at = None
        self.changed.emit(self.state())

    def apply_settings(self, settings: PomodoroSettings) -> None:
        old_duration = self.total_seconds
        self.settings = settings
        self.total_seconds = self._seconds_for_mode(self.mode)
        if self._is_overtime:
            # Don't reset overtime on settings change.
            self.time_left = 0
        elif old_duration != self.total_seconds:
            self.time_left = self.total_seconds
            self.paused = True
            self._started = False
            self._deadline = None
        elif not self.paused and self._started:
            self._deadline = self._make_deadline(self.time_left)
        self.changed.emit(self.state())

    def toggle_pause(self) -> None:
        if self.paused:
            was_started = self._started
            was_fresh_pomodoro = (
                not self._is_overtime
                and self.mode == MODE_POMODORO
                and self.time_left == self.total_seconds
            )
            self._started = True
            self.paused = False
            if self._is_overtime:
                self._overtime_started_at = time.monotonic() - self._overtime_seconds
                self._deadline = None
            else:
                self._deadline = self._make_deadline(self.time_left)
            self.changed.emit(self.state())
            if was_fresh_pomodoro and not was_started:
                # First "Play" on a fresh Pomodoro counts as starting that mode.
                self.mode_started.emit(self.mode)
            return
        self._sync_running_time_left()
        self._sync_overtime_seconds()
        self.paused = True
        self._deadline = None
        self._overtime_started_at = None
        self.changed.emit(self.state())

    def stop(self) -> None:
        self.paused = True
        self.time_left = self.total_seconds
        self._started = False
        self._deadline = None
        self._is_overtime = False
        self._overtime_seconds = 0
        self._overtime_started_at = None
        self.changed.emit(self.state())

    def suspend(self) -> None:
        """Pause countdown work without resetting the persisted timer state."""
        self._sync_running_time_left()
        self._sync_overtime_seconds()
        self.paused = True
        self._deadline = None
        self._overtime_started_at = None

    def shutdown(self) -> None:
        self._timer.stop()

    def start_mode(self, mode: str) -> None:
        self.mode = MODE_BREAK if mode == MODE_BREAK else MODE_POMODORO
        self.total_seconds = self._seconds_for_mode(self.mode)
        self.time_left = self.total_seconds
        self.paused = False
        self._started = True
        self._deadline = self._make_deadline(self.time_left)
        self._is_overtime = False
        self._overtime_seconds = 0
        self._overtime_started_at = None
        self.changed.emit(self.state())
        self.mode_started.emit(self.mode)

    def prepare_mode(self, mode: str) -> None:
        self.mode = MODE_BREAK if mode == MODE_BREAK else MODE_POMODORO
        self.total_seconds = self._seconds_for_mode(self.mode)
        self.time_left = self.total_seconds
        self.paused = True
        self._started = False
        self._deadline = None
        self._is_overtime = False
        self._overtime_seconds = 0
        self._overtime_started_at = None
        self.changed.emit(self.state())

    def start_overtime(self) -> None:
        """Continue the current Pomodoro past its target time, counting up."""
        self.mode = MODE_POMODORO
        self.total_seconds = self._seconds_for_mode(self.mode)
        self.time_left = 0
        self.paused = False
        self._started = True
        self._deadline = None
        self._is_overtime = True
        self._overtime_seconds = 0
        self._overtime_started_at = time.monotonic()
        self.changed.emit(self.state())

    def _tick(self) -> None:
        if self.paused:
            return

        if self._is_overtime:
            self._sync_overtime_seconds()
            self.changed.emit(self.state())
            return

        self._sync_running_time_left()
        self.changed.emit(self.state())
        if self.time_left <= 0:
            self._complete_current_mode()

    def _complete_current_mode(self) -> None:
        if self.mode == MODE_POMODORO:
            self.pomodoro_completed.emit()
            if self.settings.auto_start_break:
                self.start_mode(MODE_BREAK)
            else:
                self.paused = True
                self._started = False
                self._deadline = None
                self.changed.emit(self.state())
                self.pomodoro_done.emit()
            return

        self.break_completed.emit()
        if self.settings.auto_start_pomodoro_after_break:
            self.start_mode(MODE_POMODORO)
            return

        self.prepare_mode(MODE_POMODORO)
        self.break_done.emit()

    def _seconds_for_mode(self, mode: str) -> int:
        minutes = self.settings.break_minutes if mode == MODE_BREAK else self.settings.pomodoro_minutes
        return max(1, int(minutes)) * 60

    def _sync_running_time_left(self) -> None:
        if self.paused or self._deadline is None or self._is_overtime:
            return
        self.time_left = max(0, min(self.total_seconds, math.ceil(self._deadline - time.monotonic())))

    def _sync_overtime_seconds(self) -> None:
        if not self._is_overtime or self.paused or self._overtime_started_at is None:
            return
        elapsed = int(time.monotonic() - self._overtime_started_at)
        self._overtime_seconds = max(0, min(24 * 60 * 60, elapsed))

    def _make_deadline(self, seconds: int) -> float:
        return time.monotonic() + max(0, int(seconds))
