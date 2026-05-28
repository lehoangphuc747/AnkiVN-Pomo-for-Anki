"""Settings dialog for the Pomodoro add-on."""

from __future__ import annotations

from aqt.qt import (
    QCheckBox,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QSize,
    QSlider,
    QSpinBox,
    Qt,
    QVBoxLayout,
    QWidget,
    pyqtSignal,
)

from .color_presets import CUSTOM_PRESET_ID, DEFAULT_PRESET_ID, PRESETS, get_preset
from .i18n import DEFAULT_LANGUAGE, available_languages, tr
from .models import LAYOUT_CORNER, LAYOUT_SIDEBAR, LAYOUT_UNDER, SIDEBAR_LEFT, SIDEBAR_RIGHT, THEME_DARK, THEME_LIGHT, THEME_SYSTEM, PomodoroSettings
from .style import DEFAULT_ACCENT_DARK, DEFAULT_ACCENT_LIGHT
from .ui_components import PillSwitcher, VIETNAM_ICON_PATH, make_button, make_icon_label, make_label, set_addon_window_icon


class SettingsDialog(QDialog):
    apply_requested = pyqtSignal()
    export_requested = pyqtSignal()
    import_requested = pyqtSignal()
    reset_data_requested = pyqtSignal()
    reset_all_requested = pyqtSignal()

    def __init__(self, parent: QWidget, settings: PomodoroSettings) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("settings.title"))
        set_addon_window_icon(self)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setMinimumSize(420, 400)
        saved_w = settings.dialog_width or 520
        saved_h = settings.dialog_height or 680
        self.resize(saved_w, saved_h)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        self.layout_switcher = PillSwitcher(self)
        self.layout_switcher.add_option(tr("layout.under"), LAYOUT_UNDER)
        self.layout_switcher.add_option(tr("layout.sidebar"), LAYOUT_SIDEBAR)
        self.layout_switcher.add_option(tr("layout.corner"), LAYOUT_CORNER)
        self.layout_switcher.set_current_value(settings.layout)

        self.sidebar_side_switcher = PillSwitcher(self)
        self.sidebar_side_switcher.add_option(tr("settings.sidebar_left"), SIDEBAR_LEFT)
        self.sidebar_side_switcher.add_option(tr("settings.sidebar_right"), SIDEBAR_RIGHT)
        self.sidebar_side_switcher.set_current_value(settings.sidebar_side)
        self.layout_switcher.selectionChanged.connect(self._on_layout_changed)
        self._sidebar_side_visible = settings.layout == LAYOUT_SIDEBAR

        self.theme_switcher = PillSwitcher(self)
        self.theme_switcher.add_option(tr("settings.theme_system"), THEME_SYSTEM)
        self.theme_switcher.add_option(tr("settings.theme_light"), THEME_LIGHT)
        self.theme_switcher.add_option(tr("settings.theme_dark"), THEME_DARK)
        self.theme_switcher.set_current_value(settings.theme)

        # Color preset dropdown + accent swatch.
        self._current_preset_id: str = settings.color_preset or DEFAULT_PRESET_ID
        self._accent_value: str = (settings.accent_color or "").upper()
        self.preset_combo = QComboBox()
        for preset in PRESETS:
            self.preset_combo.addItem(tr(preset.label_key), preset.id)
        self.preset_combo.addItem(tr("preset.custom"), CUSTOM_PRESET_ID)
        preset_index = self.preset_combo.findData(self._current_preset_id)
        if preset_index >= 0:
            self.preset_combo.setCurrentIndex(preset_index)
        else:
            self.preset_combo.setCurrentIndex(0)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        self.accent_swatch = QPushButton()
        self.accent_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accent_swatch.setFixedSize(QSize(34, 26))
        self.accent_swatch.setToolTip(tr("settings.accent_pick_tooltip"))
        self.accent_swatch.clicked.connect(self._open_accent_picker)

        # Break color swatch.
        self._break_color_value: str = (settings.break_color or "").upper()
        self.break_swatch = QPushButton()
        self.break_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.break_swatch.setFixedSize(QSize(34, 26))
        self.break_swatch.setToolTip(tr("settings.break_color_tooltip"))
        self.break_swatch.clicked.connect(self._open_break_picker)

        # Background tint swatch.
        self._bg_tint_value: str = (settings.bg_tint or "").upper()
        self.bg_tint_swatch = QPushButton()
        self.bg_tint_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bg_tint_swatch.setFixedSize(QSize(34, 26))
        self.bg_tint_swatch.setToolTip(tr("settings.bg_tint_tooltip"))
        self.bg_tint_swatch.clicked.connect(self._open_bg_tint_picker)

        self._refresh_accent_swatch()
        self._refresh_break_swatch()
        self._refresh_bg_tint_swatch()

        # Background image controls.
        self._bg_image_path: str = str(getattr(settings, "bg_image_path", "") or "")
        self.bg_image_button = make_button(tr("settings.bg_image_choose"), "secondary", tr("settings.bg_image_choose_tooltip"))
        self.bg_image_button.clicked.connect(self._choose_bg_image)
        self.bg_image_clear_button = make_button(tr("settings.bg_image_clear"), "secondary", tr("settings.bg_image_clear_tooltip"))
        self.bg_image_clear_button.clicked.connect(self._clear_bg_image)
        self.bg_image_label = make_label(self._format_bg_image_label(), "muted")

        self.bg_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.bg_opacity_slider.setRange(0, 60)
        self.bg_opacity_slider.setValue(int(getattr(settings, "bg_image_opacity", 18) or 18))
        self.bg_opacity_slider.setMinimumWidth(120)
        self.bg_opacity_value_label = make_label(self._format_percent(self.bg_opacity_slider.value()), "muted")
        self.bg_opacity_slider.valueChanged.connect(
            lambda v: self.bg_opacity_value_label.setText(self._format_percent(v))
        )

        self.bg_blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.bg_blur_slider.setRange(0, 30)
        self.bg_blur_slider.setValue(int(getattr(settings, "bg_image_blur", 8) or 0))
        self.bg_blur_slider.setMinimumWidth(120)
        self.bg_blur_value_label = make_label(f"{self.bg_blur_slider.value()}px", "muted")
        self.bg_blur_slider.valueChanged.connect(
            lambda v: self.bg_blur_value_label.setText(f"{v}px")
        )

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
            (tr("settings.layout"), self.layout_switcher),
            (tr("settings.pomodoro_time"), self.pomodoro_spin),
            (tr("settings.break_time"), self.break_spin),
            (tr("settings.theme"), self.theme_switcher),
            (tr("settings.language"), self.language_combo),
        ]:
            row = QHBoxLayout()
            row.addWidget(make_label(label))
            row.addStretch(1)
            row.addWidget(widget)
            root.addLayout(row)

        accent_row = QHBoxLayout()
        accent_row.addWidget(make_label(tr("settings.accent_color")))
        accent_row.addStretch(1)
        accent_row.addWidget(self.preset_combo)
        accent_row.addSpacing(6)
        accent_row.addWidget(self.accent_swatch)
        accent_row.addSpacing(4)
        accent_row.addWidget(self.break_swatch)
        accent_row.addSpacing(4)
        accent_row.addWidget(self.bg_tint_swatch)
        root.addLayout(accent_row)

        # Background image row 1: choose / clear + label
        bg_image_row = QHBoxLayout()
        bg_image_row.addWidget(make_label(tr("settings.bg_image")))
        bg_image_row.addStretch(1)
        bg_image_row.addWidget(self.bg_image_button)
        bg_image_row.addSpacing(4)
        bg_image_row.addWidget(self.bg_image_clear_button)
        root.addLayout(bg_image_row)

        bg_image_label_row = QHBoxLayout()
        bg_image_label_row.addStretch(1)
        bg_image_label_row.addWidget(self.bg_image_label)
        root.addLayout(bg_image_label_row)

        # Background image row 2: opacity slider
        bg_opacity_row = QHBoxLayout()
        bg_opacity_row.addWidget(make_label(tr("settings.bg_image_opacity"), "muted"))
        bg_opacity_row.addWidget(self.bg_opacity_slider, 1)
        bg_opacity_row.addWidget(self.bg_opacity_value_label)
        root.addLayout(bg_opacity_row)

        # Background image row 3: blur slider
        bg_blur_row = QHBoxLayout()
        bg_blur_row.addWidget(make_label(tr("settings.bg_image_blur"), "muted"))
        bg_blur_row.addWidget(self.bg_blur_slider, 1)
        bg_blur_row.addWidget(self.bg_blur_value_label)
        root.addLayout(bg_blur_row)

        self.sidebar_side_row = QHBoxLayout()
        self.sidebar_side_row.addWidget(make_label(tr("settings.sidebar_position")))
        self.sidebar_side_row.addStretch(1)
        self.sidebar_side_row.addWidget(self.sidebar_side_switcher)
        root.addLayout(self.sidebar_side_row)
        self._update_sidebar_side_visibility()

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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        apply_button = buttons.button(QDialogButtonBox.StandardButton.Apply)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button:
            ok_button.setText(tr("common.ok"))
        if apply_button:
            apply_button.setText(tr("common.apply"))
        if cancel_button:
            cancel_button.setText(tr("common.cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if apply_button:
            apply_button.clicked.connect(lambda _checked=False: self.apply_requested.emit())
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
        s = self.size()
        return PomodoroSettings(
            layout=str(self.layout_switcher.current_value() or previous.layout),
            sidebar_side=str(self.sidebar_side_switcher.current_value() or previous.sidebar_side),
            theme=str(self.theme_switcher.current_value() or previous.theme),
            accent_color=self._accent_value,
            break_color=self._break_color_value,
            bg_tint=self._bg_tint_value,
            bg_image_path=self._bg_image_path,
            bg_image_opacity=int(self.bg_opacity_slider.value()),
            bg_image_blur=int(self.bg_blur_slider.value()),
            color_preset=self._current_preset_id,
            pomodoro_minutes=int(self.pomodoro_spin.value()),
            break_minutes=int(self.break_spin.value()),
            auto_start_break=bool(self.auto_break.isChecked()),
            auto_start_pomodoro_after_break=bool(self.auto_pomodoro_after_break.isChecked()),
            language=str(self.language_combo.currentData() or previous.language),
            corner_left=previous.corner_left,
            corner_top=previous.corner_top,
            dialog_width=s.width(),
            dialog_height=s.height(),
        )

    def _on_preset_changed(self, _index: int) -> None:
        preset_id = self.preset_combo.currentData()
        if not preset_id:
            return
        self._current_preset_id = str(preset_id)
        if self._current_preset_id != CUSTOM_PRESET_ID:
            preset = get_preset(self._current_preset_id)
            if preset:
                self._accent_value = preset.accent.upper()
                self._break_color_value = ""  # Use preset break color
                self._bg_tint_value = ""  # Use preset bg tint
        self._refresh_accent_swatch()
        self._refresh_break_swatch()
        self._refresh_bg_tint_swatch()

    def _open_accent_picker(self) -> None:
        current = QColor(self._accent_value) if self._accent_value else QColor(self._effective_default_accent())
        if not current.isValid():
            current = QColor(self._effective_default_accent())
        chosen = QColorDialog.getColor(current, self, tr("settings.accent_pick_title"))
        if not chosen.isValid():
            return
        self._accent_value = chosen.name().upper()
        self._switch_to_custom()
        self._refresh_accent_swatch()

    def _open_break_picker(self) -> None:
        current_color = self._break_color_value or self._effective_break_from_preset()
        current = QColor(current_color)
        if not current.isValid():
            current = QColor("#739E73")
        chosen = QColorDialog.getColor(current, self, tr("settings.break_color_pick_title"))
        if not chosen.isValid():
            return
        self._break_color_value = chosen.name().upper()
        self._switch_to_custom()
        self._refresh_break_swatch()

    def _switch_to_custom(self) -> None:
        """Switch preset dropdown to Custom when user picks a custom color."""
        self._current_preset_id = CUSTOM_PRESET_ID
        custom_index = self.preset_combo.findData(CUSTOM_PRESET_ID)
        if custom_index >= 0:
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentIndex(custom_index)
            self.preset_combo.blockSignals(False)

    def _refresh_accent_swatch(self) -> None:
        color = self._accent_value or self._effective_default_accent()
        self.accent_swatch.setText("")
        self.accent_swatch.setStyleSheet(
            f"""
            QPushButton {{
                background: {color};
                border: 1px solid rgba(0, 0, 0, 0.18);
                border-radius: 6px;
            }}
            QPushButton:hover {{
                border: 1px solid rgba(0, 0, 0, 0.42);
            }}
            """
        )
        if self._accent_value:
            self.accent_swatch.setToolTip(tr("settings.accent_pick_tooltip_value", value=self._accent_value))
        else:
            self.accent_swatch.setToolTip(tr("settings.accent_pick_tooltip"))

    def _refresh_break_swatch(self) -> None:
        color = self._break_color_value or self._effective_break_from_preset()
        self.break_swatch.setText("")
        self.break_swatch.setStyleSheet(
            f"""
            QPushButton {{
                background: {color};
                border: 1px solid rgba(0, 0, 0, 0.18);
                border-radius: 6px;
            }}
            QPushButton:hover {{
                border: 1px solid rgba(0, 0, 0, 0.42);
            }}
            """
        )
        if self._break_color_value:
            self.break_swatch.setToolTip(tr("settings.break_color_tooltip_value", value=self._break_color_value))
        else:
            self.break_swatch.setToolTip(tr("settings.break_color_tooltip"))

    def _effective_break_from_preset(self) -> str:
        if self._current_preset_id and self._current_preset_id != CUSTOM_PRESET_ID:
            preset = get_preset(self._current_preset_id)
            if preset:
                return preset.break_color
        return "#739E73"

    def _open_bg_tint_picker(self) -> None:
        current_color = self._bg_tint_value or self._effective_bg_tint_from_preset() or "#F8F7F3"
        current = QColor(current_color)
        if not current.isValid():
            current = QColor("#F8F7F3")
        chosen = QColorDialog.getColor(current, self, tr("settings.bg_tint_pick_title"))
        if not chosen.isValid():
            return
        self._bg_tint_value = chosen.name().upper()
        self._switch_to_custom()
        self._refresh_bg_tint_swatch()

    def _refresh_bg_tint_swatch(self) -> None:
        color = self._bg_tint_value or self._effective_bg_tint_from_preset() or "#F8F7F3"
        self.bg_tint_swatch.setText("")
        self.bg_tint_swatch.setStyleSheet(
            f"""
            QPushButton {{
                background: {color};
                border: 1px solid rgba(0, 0, 0, 0.18);
                border-radius: 6px;
            }}
            QPushButton:hover {{
                border: 1px solid rgba(0, 0, 0, 0.42);
            }}
            """
        )
        if self._bg_tint_value:
            self.bg_tint_swatch.setToolTip(tr("settings.bg_tint_tooltip_value", value=self._bg_tint_value))
        else:
            self.bg_tint_swatch.setToolTip(tr("settings.bg_tint_tooltip"))

    def _effective_bg_tint_from_preset(self) -> str:
        if self._current_preset_id and self._current_preset_id != CUSTOM_PRESET_ID:
            preset = get_preset(self._current_preset_id)
            if preset:
                return preset.bg_tint
        return ""

    # --- Background image ----------------------------------------------------

    def _choose_bg_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("settings.bg_image_pick_title"),
            self._bg_image_path or "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif);;All files (*.*)",
        )
        if not path:
            return
        self._bg_image_path = str(path)
        self.bg_image_label.setText(self._format_bg_image_label())

    def _clear_bg_image(self) -> None:
        self._bg_image_path = ""
        self.bg_image_label.setText(self._format_bg_image_label())

    def _format_bg_image_label(self) -> str:
        if not self._bg_image_path:
            return tr("settings.bg_image_none")
        from pathlib import Path
        return Path(self._bg_image_path).name

    def _format_percent(self, value: int) -> str:
        return f"{int(value)}%"

    def _effective_default_accent(self) -> str:
        theme_value = self.theme_switcher.current_value()
        if theme_value == THEME_DARK:
            return DEFAULT_ACCENT_DARK
        return DEFAULT_ACCENT_LIGHT

    def _on_layout_changed(self, value: object) -> None:
        self._sidebar_side_visible = value == LAYOUT_SIDEBAR
        self._update_sidebar_side_visibility()

    def _update_sidebar_side_visibility(self) -> None:
        self.sidebar_side_switcher.setVisible(self._sidebar_side_visible)
        # Walk the sidebar_side_row and hide/show all widgets
        for i in range(self.sidebar_side_row.count()):
            item = self.sidebar_side_row.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(self._sidebar_side_visible)
