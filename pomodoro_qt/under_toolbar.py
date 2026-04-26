"""Under-toolbar Pomodoro layout."""

from __future__ import annotations

from typing import Iterable

from aqt.qt import QFrame, QHBoxLayout, QProgressBar, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from .i18n import tr
from .models import PomodoroTimerState, SessionMetrics
from .style import COLORS
from .ui_components import (
    ALIGN_CENTER,
    SYMBOL_FIRE,
    SYMBOL_LIGHTNING,
    SYMBOL_SPARKLE,
    SYMBOL_TOMATO,
    make_label,
    make_pause_button,
    make_session_dots_text,
    make_settings_button,
    make_sound_button,
    make_stop_button,
    make_toolbar_metric_button,
    mode_label_text,
    set_accent_property,
    set_pause_button_state,
)


class UnderToolbarWidget(QFrame):
    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__()
        self.metrics = metrics
        self.setProperty("panel", "under")
        self.setFixedHeight(64)

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 2, 24, 5)
        root.setSpacing(20)

        left = QHBoxLayout()
        left.setSpacing(18)
        self.mode_label = make_label(f"{SYMBOL_TOMATO} {tr('mode.pomodoro').upper()}", "mode")
        self.session_button = make_toolbar_metric_button(self._session_text(metrics), COLORS["muted"], tr("tooltip.session_history"))
        self.experience_button = make_toolbar_metric_button(
            self._experience_text(metrics),
            COLORS["text"],
            tr("tooltip.experience"),
            650,
        )
        left.addWidget(self.mode_label)
        left.addWidget(self.session_button)
        left.addWidget(self.experience_button)
        left.addStretch(1)

        center = QVBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(7)
        self.timer_label = make_label("25:00", "timer")
        self.timer_label.setAlignment(ALIGN_CENTER)
        self.timer_label.setFixedHeight(34)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(144)
        self.progress.setFixedHeight(6)
        center.addWidget(self.timer_label, 0, ALIGN_CENTER)
        center.addWidget(self.progress, 0, ALIGN_CENTER)

        right = QHBoxLayout()
        right.setSpacing(0)
        right.setContentsMargins(0, 0, 0, 0)
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(4)
        metrics_row.setContentsMargins(0, 0, 0, 0)
        controls_row = QHBoxLayout()
        controls_row.setSpacing(14)
        controls_row.setContentsMargins(0, 0, 0, 0)

        self.streak_button = make_toolbar_metric_button(
            f"{SYMBOL_FIRE} {tr('metric.day_short', count=metrics.streak_days)}",
            COLORS["muted"],
            tr("tooltip.streak"),
        )
        self.cards_button = make_toolbar_metric_button(
            f"{SYMBOL_LIGHTNING} {tr('metric.cards_short', count=metrics.cards)}", COLORS["red"], tr("tooltip.cards")
        )
        self.retention_button = make_toolbar_metric_button(
            tr("common.percent", value=metrics.retention), COLORS["green"], tr("tooltip.retention"), 650
        )
        self.pause_button = make_pause_button()
        self.stop_button = make_stop_button(COLORS["muted"], 14)
        self.audio_button = make_sound_button(COLORS["muted"], 17)
        self.settings_button = make_settings_button(COLORS["muted"], 16)

        for button in [self.streak_button, self.cards_button, self.retention_button]:
            metrics_row.addWidget(button)
        for button in [self.pause_button, self.stop_button, self.audio_button, self.settings_button]:
            controls_row.addWidget(button)

        right.addStretch(1)
        right.addLayout(metrics_row)
        right.addSpacing(16)
        right.addLayout(controls_row)

        left_box = QWidget()
        left_box.setLayout(left)
        left_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        center_box = QWidget()
        center_box.setLayout(center)
        center_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        right_box = QWidget()
        right_box.setLayout(right)
        right_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        root.addWidget(left_box, 1)
        root.addWidget(center_box, 0)
        root.addWidget(right_box, 1)

    def sync_state(self, state: PomodoroTimerState) -> None:
        self.mode_label.setText(mode_label_text(state))
        self.timer_label.setText(state.time_text)
        self.progress.setValue(int(state.progress * 1000))
        set_accent_property(self.mode_label, state.accent)
        set_accent_property(self.timer_label, state.accent)
        set_pause_button_state(self.pause_button, state.paused)
        self.stop_button.setVisible(state.started)

    def refresh_metrics(self, metrics: SessionMetrics) -> None:
        self.metrics = metrics
        self.session_button.setText(self._session_text(metrics))
        self.experience_button.setText(self._experience_text(metrics))
        self.streak_button.setText(f"{SYMBOL_FIRE} {tr('metric.day_short', count=metrics.streak_days)}")
        self.retention_button.setText(tr("common.percent", value=metrics.retention))
        self.cards_button.setText(f"{SYMBOL_LIGHTNING} {tr('metric.cards_short', count=metrics.cards)}")

    def metric_buttons(self) -> Iterable[QPushButton]:
        return [
            self.session_button,
            self.experience_button,
            self.cards_button,
            self.streak_button,
            self.retention_button,
        ]

    def _session_text(self, metrics: SessionMetrics) -> str:
        return make_session_dots_text(metrics)

    def _experience_text(self, metrics: SessionMetrics) -> str:
        return f"{tr('metric.level_short')} {metrics.level} {metrics.total_xp}/{metrics.next_level_xp} {SYMBOL_SPARKLE}"
