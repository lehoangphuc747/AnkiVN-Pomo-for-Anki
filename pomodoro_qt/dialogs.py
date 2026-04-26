"""Dialog widgets used by Pomodoro controller flows."""

from __future__ import annotations

from aqt.qt import QDialog, QHBoxLayout, QVBoxLayout, QWidget

from .i18n import tr
from .models import MODE_BREAK, MODE_POMODORO, PomodoroSettings, SessionMetrics
from .style import COLORS
from .ui_components import ALIGN_CENTER, make_button, make_label


class PomodoroDoneDialog(QDialog):
    def __init__(self, parent: QWidget, settings: PomodoroSettings, metrics: SessionMetrics) -> None:
        super().__init__(parent)
        self.choice = MODE_BREAK
        self.setWindowTitle(tr("dialog.done_title"))
        self.setModal(True)
        self.setMinimumWidth(440)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(16)

        title = make_label(tr("dialog.done_title"))
        title.setAlignment(ALIGN_CENTER)
        title.setStyleSheet(f"font-size: 42px; font-weight: 650; color: {COLORS['red']};")
        subtitle = make_label(
            tr("dialog.done_subtitle", cards=metrics.cards, retention=metrics.retention, xp=metrics.session_xp),
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
        actions.addStretch(1)
        actions.addWidget(keep_going)
        actions.addWidget(take_break)
        actions.addStretch(1)
        root.addLayout(actions)

        keep_going.clicked.connect(self._keep_going)
        take_break.clicked.connect(self._take_break)

    def _keep_going(self) -> None:
        self.choice = MODE_POMODORO
        self.accept()

    def _take_break(self) -> None:
        self.choice = MODE_BREAK
        self.accept()
