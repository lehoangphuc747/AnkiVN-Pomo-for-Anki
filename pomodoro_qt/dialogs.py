"""Dialog widgets used by Pomodoro controller flows."""

from __future__ import annotations

from aqt.qt import QDialog, QHBoxLayout, QVBoxLayout, QWidget

from .i18n import tr
from .models import MODE_BREAK, MODE_POMODORO, PomodoroSettings, SessionMetrics
from .style import COLORS
from .ui_components import ALIGN_CENTER, make_button, make_label, set_addon_window_icon


CHOICE_END = "end"


class PomodoroDoneDialog(QDialog):
    def __init__(self, parent: QWidget, settings: PomodoroSettings, metrics: SessionMetrics) -> None:
        super().__init__(parent)
        self.choice = MODE_BREAK
        self.setWindowTitle(tr("dialog.done_title"))
        set_addon_window_icon(self)
        self.setModal(True)
        self.setMinimumWidth(440)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(16)

        title = make_label(tr("dialog.done_title"))
        title.setAlignment(ALIGN_CENTER)
        title.setStyleSheet(f"font-size: 42px; font-weight: 650; color: {COLORS['red']};")
        subtitle = make_label(
            tr(
                "dialog.done_subtitle",
                cards=metrics.session_cards,
                retention=metrics.session_retention,
                xp=metrics.session_xp,
            ),
            "muted",
        )
        subtitle.setAlignment(ALIGN_CENTER)
        subtitle.setStyleSheet("font-size: 15px; font-weight: 550; color: #6B6661;")
        root.addWidget(title)
        root.addWidget(subtitle)

        actions = QHBoxLayout()
        actions.setSpacing(16)
        keep_going = make_button(tr("action.keep_going"), "secondary")
        take_break = make_button(tr("action.take_break", minutes=settings.break_minutes), "primary")
        end_session = make_button(tr("action.end"), "secondary")
        actions.addStretch(1)
        actions.addWidget(keep_going)
        actions.addWidget(take_break)
        actions.addWidget(end_session)
        actions.addStretch(1)
        root.addLayout(actions)

        keep_going.clicked.connect(self._keep_going)
        take_break.clicked.connect(self._take_break)
        end_session.clicked.connect(self._end_session)

    def _keep_going(self) -> None:
        self.choice = MODE_POMODORO
        self.accept()

    def _take_break(self) -> None:
        self.choice = MODE_BREAK
        self.accept()

    def _end_session(self) -> None:
        self.choice = CHOICE_END
        self.accept()


class BreakDoneDialog(QDialog):
    def __init__(self, parent: QWidget, settings: PomodoroSettings) -> None:
        super().__init__(parent)
        self.choice = MODE_POMODORO
        self.setWindowTitle(tr("dialog.break_done_title"))
        set_addon_window_icon(self)
        self.setModal(True)
        self.setMinimumWidth(440)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(16)

        title = make_label(tr("dialog.break_done_title"))
        title.setAlignment(ALIGN_CENTER)
        title.setStyleSheet(f"font-size: 42px; font-weight: 650; color: {COLORS['green']};")
        subtitle = make_label(tr("dialog.break_done_subtitle", minutes=settings.pomodoro_minutes), "muted")
        subtitle.setAlignment(ALIGN_CENTER)
        subtitle.setStyleSheet("font-size: 15px; font-weight: 550; color: #6B6661;")
        root.addWidget(title)
        root.addWidget(subtitle)

        actions = QHBoxLayout()
        actions.setSpacing(16)
        start_pomodoro = make_button(tr("action.start_pomodoro", minutes=settings.pomodoro_minutes), "primary")
        end_session = make_button(tr("action.end"), "secondary")
        actions.addStretch(1)
        actions.addWidget(start_pomodoro)
        actions.addWidget(end_session)
        actions.addStretch(1)
        root.addLayout(actions)

        start_pomodoro.clicked.connect(self._start_pomodoro)
        end_session.clicked.connect(self._end_session)

    def _start_pomodoro(self) -> None:
        self.choice = MODE_POMODORO
        self.accept()

    def _end_session(self) -> None:
        self.choice = CHOICE_END
        self.accept()
