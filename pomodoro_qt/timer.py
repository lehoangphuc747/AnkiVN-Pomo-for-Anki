"""Pomodoro timer state machine backed by Qt's event loop."""

from __future__ import annotations

from aqt.qt import QObject, QTimer, pyqtSignal

from datetime import datetime

from .models import MODE_BREAK, MODE_POMODORO, PomodoroSettings, PomodoroTimerState, TimerRuntimeState


class PomodoroTimer(QObject):
    changed = pyqtSignal(object)
    pomodoro_completed = pyqtSignal()
    break_completed = pyqtSignal()
    pomodoro_done = pyqtSignal()

    def __init__(self, settings: PomodoroSettings) -> None:
        super().__init__()
        self.settings = settings
        self.mode = MODE_POMODORO
        self.total_seconds = self._seconds_for_mode(self.mode)
        self.time_left = self.total_seconds
        self.paused = True
        self._started = False
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def state(self) -> PomodoroTimerState:
        return PomodoroTimerState(
            mode=self.mode,
            total_seconds=self.total_seconds,
            time_left=self.time_left,
            paused=self.paused,
            started=self._started,
        )

    def runtime_state(self) -> TimerRuntimeState:
        return TimerRuntimeState(
            mode=self.mode,
            total_seconds=self.total_seconds,
            time_left=self.time_left,
            paused=self.paused,
            started=self._started,
            saved_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        )

    def restore_state(self, state: TimerRuntimeState) -> None:
        self.mode = MODE_BREAK if state.mode == MODE_BREAK else MODE_POMODORO
        configured_total = self._seconds_for_mode(self.mode)
        self.total_seconds = configured_total
        self.time_left = max(0, min(configured_total, int(state.time_left)))
        self.paused = bool(state.paused)
        self._started = bool(state.started or not self.paused or self.time_left < self.total_seconds)
        self.changed.emit(self.state())

    def apply_settings(self, settings: PomodoroSettings) -> None:
        old_duration = self.total_seconds
        self.settings = settings
        self.total_seconds = self._seconds_for_mode(self.mode)
        if old_duration != self.total_seconds:
            self.time_left = self.total_seconds
            self.paused = True
            self._started = False
        self.changed.emit(self.state())

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if not self.paused:
            self._started = True
        self.changed.emit(self.state())

    def stop(self) -> None:
        self.paused = True
        self.time_left = self.total_seconds
        self._started = False
        self.changed.emit(self.state())

    def start_mode(self, mode: str) -> None:
        self.mode = MODE_BREAK if mode == MODE_BREAK else MODE_POMODORO
        self.total_seconds = self._seconds_for_mode(self.mode)
        self.time_left = self.total_seconds
        self.paused = False
        self._started = True
        self.changed.emit(self.state())

    def _tick(self) -> None:
        if self.paused:
            return

        if self.time_left > 0:
            self.time_left -= 1
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
                self.changed.emit(self.state())
                self.pomodoro_done.emit()
            return

        self.break_completed.emit()
        self.start_mode(MODE_POMODORO)

    def _seconds_for_mode(self, mode: str) -> int:
        minutes = self.settings.break_minutes if mode == MODE_BREAK else self.settings.pomodoro_minutes
        return max(1, int(minutes)) * 60
