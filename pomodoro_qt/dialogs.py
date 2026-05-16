"""Dialog widgets used by Pomodoro controller flows."""

from __future__ import annotations

from aqt.qt import QDialog, QDialogButtonBox, QHBoxLayout, QSpinBox, QVBoxLayout, QWidget

from .i18n import format_number, tr
from .models import MODE_BREAK, MODE_POMODORO, PomodoroSettings, SessionMetrics
from .style import COLORS
from .ui_components import ALIGN_CENTER, make_button, make_label, set_addon_window_icon


CHOICE_END = "end"


class PomodoroDoneDialog(QDialog):
    def __init__(self, parent: QWidget, settings: PomodoroSettings, metrics: SessionMetrics) -> None:
        super().__init__(parent)
        self.choice = MODE_BREAK
        self.break_minutes = int(settings.break_minutes)
        self.pomodoro_minutes = int(settings.pomodoro_minutes)
        self.setWindowTitle(tr("dialog.done_title"))
        set_addon_window_icon(self)
        self.setModal(True)
        self.setMinimumWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(16)

        title = make_label(tr("dialog.done_title"))
        title.setAlignment(ALIGN_CENTER)
        title.setStyleSheet(f"font-size: 42px; font-weight: 650; color: {COLORS['red']};")
        subtitle = make_label(
            tr(
                "dialog.done_subtitle",
                cards=format_number(metrics.session_cards),
                retention=format_number(metrics.session_retention),
                xp=format_number(metrics.session_xp),
            ),
            "muted",
        )
        subtitle.setAlignment(ALIGN_CENTER)
        subtitle.setStyleSheet("font-size: 15px; font-weight: 550; color: #6B6661;")
        root.addWidget(title)
        root.addWidget(subtitle)

        # Break minutes input row
        break_row = QHBoxLayout()
        break_row.setSpacing(8)
        break_row.addStretch(1)
        break_row.addWidget(make_label(tr("dialog.break_minutes_label"), "muted"))
        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 60)
        self.break_spin.setValue(int(settings.break_minutes))
        self.break_spin.setSuffix(tr("common.minute_suffix"))
        self.break_spin.valueChanged.connect(self._on_break_minutes_changed)
        break_row.addWidget(self.break_spin)
        break_row.addStretch(1)
        root.addLayout(break_row)

        actions = QHBoxLayout()
        actions.setSpacing(16)
        keep_going = make_button(tr("action.keep_going"), "secondary")
        self.take_break_button = make_button(
            tr("action.take_break", minutes=format_number(settings.break_minutes)),
            "primary",
        )
        end_session = make_button(tr("action.end"), "secondary")
        actions.addStretch(1)
        actions.addWidget(keep_going)
        actions.addWidget(self.take_break_button)
        actions.addWidget(end_session)
        actions.addStretch(1)
        root.addLayout(actions)

        keep_going.clicked.connect(self._keep_going)
        self.take_break_button.clicked.connect(self._take_break)
        end_session.clicked.connect(self._end_session)

    def _on_break_minutes_changed(self, value: int) -> None:
        self.break_minutes = int(value)
        self.take_break_button.setText(
            tr("action.take_break", minutes=format_number(int(value)))
        )

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
        self.pomodoro_minutes = int(settings.pomodoro_minutes)
        self.setWindowTitle(tr("dialog.break_done_title"))
        set_addon_window_icon(self)
        self.setModal(True)
        self.setMinimumWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(16)

        title = make_label(tr("dialog.break_done_title"))
        title.setAlignment(ALIGN_CENTER)
        title.setStyleSheet(f"font-size: 42px; font-weight: 650; color: {COLORS['green']};")
        subtitle = make_label(tr("dialog.break_done_subtitle", minutes=format_number(settings.pomodoro_minutes)), "muted")
        subtitle.setAlignment(ALIGN_CENTER)
        subtitle.setStyleSheet("font-size: 15px; font-weight: 550; color: #6B6661;")
        root.addWidget(title)
        root.addWidget(subtitle)

        # Pomodoro minutes input row
        pom_row = QHBoxLayout()
        pom_row.setSpacing(8)
        pom_row.addStretch(1)
        pom_row.addWidget(make_label(tr("dialog.pomodoro_minutes_label"), "muted"))
        self.pomodoro_spin = QSpinBox()
        self.pomodoro_spin.setRange(1, 180)
        self.pomodoro_spin.setValue(int(settings.pomodoro_minutes))
        self.pomodoro_spin.setSuffix(tr("common.minute_suffix"))
        self.pomodoro_spin.valueChanged.connect(self._on_pomodoro_minutes_changed)
        pom_row.addWidget(self.pomodoro_spin)
        pom_row.addStretch(1)
        root.addLayout(pom_row)

        actions = QHBoxLayout()
        actions.setSpacing(16)
        self.start_pomodoro_button = make_button(
            tr("action.start_pomodoro", minutes=format_number(settings.pomodoro_minutes)),
            "primary",
        )
        end_session = make_button(tr("action.end"), "secondary")
        actions.addStretch(1)
        actions.addWidget(self.start_pomodoro_button)
        actions.addWidget(end_session)
        actions.addStretch(1)
        root.addLayout(actions)

        self.start_pomodoro_button.clicked.connect(self._start_pomodoro)
        end_session.clicked.connect(self._end_session)

    def _on_pomodoro_minutes_changed(self, value: int) -> None:
        self.pomodoro_minutes = int(value)
        self.start_pomodoro_button.setText(
            tr("action.start_pomodoro", minutes=format_number(int(value)))
        )

    def _start_pomodoro(self) -> None:
        self.choice = MODE_POMODORO
        self.accept()

    def _end_session(self) -> None:
        self.choice = CHOICE_END
        self.accept()


class EditTimeDialog(QDialog):
    """Allows the user to edit both Pomodoro and break minutes at once."""

    def __init__(self, parent: QWidget, settings: PomodoroSettings) -> None:
        super().__init__(parent)
        self.pomodoro_minutes = int(settings.pomodoro_minutes)
        self.break_minutes = int(settings.break_minutes)
        self.setWindowTitle(tr("time_dialog.title"))
        set_addon_window_icon(self)
        self.setModal(True)
        self.setMinimumWidth(360)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        pom_row = QHBoxLayout()
        pom_row.setSpacing(8)
        pom_row.addWidget(make_label(tr("time_dialog.pomodoro_label")))
        pom_row.addStretch(1)
        self.pomodoro_spin = QSpinBox()
        self.pomodoro_spin.setRange(1, 180)
        self.pomodoro_spin.setValue(int(settings.pomodoro_minutes))
        self.pomodoro_spin.setSuffix(tr("common.minute_suffix"))
        pom_row.addWidget(self.pomodoro_spin)
        root.addLayout(pom_row)

        break_row = QHBoxLayout()
        break_row.setSpacing(8)
        break_row.addWidget(make_label(tr("time_dialog.break_label")))
        break_row.addStretch(1)
        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 60)
        self.break_spin.setValue(int(settings.break_minutes))
        self.break_spin.setSuffix(tr("common.minute_suffix"))
        break_row.addWidget(self.break_spin)
        root.addLayout(break_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText(tr("common.ok"))
        if cancel_button:
            cancel_button.setText(tr("common.cancel"))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _accept(self) -> None:
        self.pomodoro_minutes = int(self.pomodoro_spin.value())
        self.break_minutes = int(self.break_spin.value())
        self.accept()
