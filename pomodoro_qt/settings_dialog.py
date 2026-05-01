"""Settings dialog for the Pomodoro add-on."""

from __future__ import annotations

from aqt.qt import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QSpinBox, QVBoxLayout, QWidget, pyqtSignal

from .i18n import DEFAULT_LANGUAGE, available_languages, tr
from .models import LAYOUT_CORNER, LAYOUT_SIDEBAR, LAYOUT_UNDER, PomodoroSettings
from .ui_components import VIETNAM_ICON_PATH, make_button, make_icon_label, make_label, set_addon_window_icon


class SettingsDialog(QDialog):
    export_requested = pyqtSignal()
    import_requested = pyqtSignal()
    reset_data_requested = pyqtSignal()
    reset_all_requested = pyqtSignal()

    def __init__(self, parent: QWidget, settings: PomodoroSettings) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("settings.title"))
        set_addon_window_icon(self)
        self.setModal(True)
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        self.layout_combo = QComboBox()
        self.layout_combo.addItem(tr("layout.under"), LAYOUT_UNDER)
        self.layout_combo.addItem(tr("layout.sidebar"), LAYOUT_SIDEBAR)
        self.layout_combo.addItem(tr("layout.corner"), LAYOUT_CORNER)
        index = self.layout_combo.findData(settings.layout)
        if index >= 0:
            self.layout_combo.setCurrentIndex(index)

        self.pomodoro_spin = QSpinBox()
        self.pomodoro_spin.setRange(1, 180)
        self.pomodoro_spin.setValue(settings.pomodoro_minutes)
        self.pomodoro_spin.setSuffix(tr("common.minute_suffix"))

        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 60)
        self.break_spin.setValue(settings.break_minutes)
        self.break_spin.setSuffix(tr("common.minute_suffix"))

        self.auto_break = QCheckBox(tr("settings.auto_start_break"))
        self.auto_break.setChecked(settings.auto_start_break)
        self.auto_pomodoro_after_break = QCheckBox(tr("settings.auto_start_pomodoro_after_break"))
        self.auto_pomodoro_after_break.setChecked(settings.auto_start_pomodoro_after_break)

        self.language_combo = QComboBox()
        for language, label in available_languages():
            self.language_combo.addItem(label, language)
        language_index = self.language_combo.findData(settings.language)
        if language_index >= 0:
            self.language_combo.setCurrentIndex(language_index)
        else:
            fallback_index = self.language_combo.findData(DEFAULT_LANGUAGE)
            if fallback_index >= 0:
                self.language_combo.setCurrentIndex(fallback_index)

        for label, widget in [
            (tr("settings.layout"), self.layout_combo),
            (tr("settings.pomodoro_time"), self.pomodoro_spin),
            (tr("settings.break_time"), self.break_spin),
            (tr("settings.language"), self.language_combo),
        ]:
            row = QHBoxLayout()
            row.addWidget(make_label(label))
            row.addStretch(1)
            row.addWidget(widget)
            root.addLayout(row)

        root.addWidget(self.auto_break)
        root.addWidget(self.auto_pomodoro_after_break)
        root.addSpacing(4)

        data_row = QHBoxLayout()
        data_row.addWidget(make_label(tr("settings.data")))
        data_row.addStretch(1)
        self.export_button = make_button(tr("backup.export_button"), "secondary", tr("backup.export_tooltip"))
        self.import_button = make_button(tr("backup.import_button"), "secondary", tr("backup.import_tooltip"))
        data_row.addWidget(self.export_button)
        data_row.addWidget(self.import_button)
        root.addLayout(data_row)

        reset_row = QHBoxLayout()
        reset_row.addStretch(1)
        self.reset_data_button = make_button(tr("reset.study_button"), "secondary", tr("reset.study_tooltip"))
        self.reset_all_button = make_button(tr("reset.all_button"), "secondary", tr("reset.all_tooltip"))
        reset_row.addWidget(self.reset_data_button)
        reset_row.addWidget(self.reset_all_button)
        root.addLayout(reset_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText(tr("common.ok"))
        if cancel_button:
            cancel_button.setText(tr("common.cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.export_button.clicked.connect(self.export_requested.emit)
        self.import_button.clicked.connect(self.import_requested.emit)
        self.reset_data_button.clicked.connect(self.reset_data_requested.emit)
        self.reset_all_button.clicked.connect(self.reset_all_requested.emit)
        root.addWidget(buttons)

        credit = QHBoxLayout()
        credit.setContentsMargins(0, 0, 0, 0)
        credit.setSpacing(6)
        credit.addStretch(1)
        credit.addWidget(make_label("Made by Phuc Lee from", "muted"))
        credit.addWidget(make_icon_label(VIETNAM_ICON_PATH, 16))
        credit.addWidget(make_label("with L0v3", "muted"))
        credit.addStretch(1)
        root.addLayout(credit)

    def to_settings(self, previous: PomodoroSettings) -> PomodoroSettings:
        return PomodoroSettings(
            layout=str(self.layout_combo.currentData()),
            pomodoro_minutes=int(self.pomodoro_spin.value()),
            break_minutes=int(self.break_spin.value()),
            auto_start_break=bool(self.auto_break.isChecked()),
            auto_start_pomodoro_after_break=bool(self.auto_pomodoro_after_break.isChecked()),
            language=str(self.language_combo.currentData() or previous.language),
            corner_left=previous.corner_left,
            corner_top=previous.corner_top,
        )
