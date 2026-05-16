"""Under-toolbar Pomodoro layout."""

from __future__ import annotations

from typing import Iterable

from aqt.qt import QFrame, QHBoxLayout, QProgressBar, QPushButton, QSizePolicy, QVBoxLayout, QWidget, Qt

from .i18n import format_number, tr
from .cards_metric import CardsStudiedMetrics
from .experience_metric import ExperienceMetrics
from .models import MODE_BREAK, PomodoroTimerState, SessionMetrics
from .retention_metric import RetentionMetrics
from .study_time_metric import StudyTimeMetrics, format_study_duration
from .streak_metric import StreakMetrics
from .style import COLORS
from .ui_components import (
    ALIGN_CENTER,
    BRAIN_ICON_PATH,
    BOLT_ICON_PATH,
    FIRE_ICON_PATH,
    GROWTH_ICON_PATH,
    HISTORY_ICON_PATH,
    STUDY_TIME_ICON_PATH,
    TOMATO_ICON_PATH,
    make_clickable_label,
    make_feedback_button,
    make_icon_text_label,
    make_pause_button,
    make_settings_button,
    make_sound_button,
    make_stop_button,
    make_toolbar_metric_button,
    mode_label_text,
    set_button_icon,
    set_accent_property,
    set_pause_button_state,
)


class UnderToolbarWidget(QFrame):
    def __init__(
        self,
        metrics: SessionMetrics,
        experience_metrics: ExperienceMetrics,
        cards_metrics: CardsStudiedMetrics,
        retention_metrics: RetentionMetrics,
        streak_metrics: StreakMetrics,
        study_time_metrics: StudyTimeMetrics,
    ) -> None:
        super().__init__()
        self.metrics = metrics
        self.experience_metrics = experience_metrics
        self.cards_metrics = cards_metrics
        self.retention_metrics = retention_metrics
        self.streak_metrics = streak_metrics
        self.study_time_metrics = study_time_metrics
        self.setProperty("panel", "under")
        self.setFixedHeight(64)

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 0, 24, 0)
        root.setSpacing(18)

        left = QHBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(12)
        self.mode_label = make_icon_text_label(
            TOMATO_ICON_PATH,
            self._brand_text(),
            "brand",
            22,
            8,
        )

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(6)
        metrics_row.setContentsMargins(0, 0, 0, 0)
        self.experience_button = make_toolbar_metric_button(
            self._experience_text(experience_metrics),
            COLORS["yellow"],
            tr("tooltip.experience"),
            650,
        )
        self.experience_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        set_button_icon(self.experience_button, GROWTH_ICON_PATH, 17)
        self.streak_button = make_toolbar_metric_button(
            self._streak_text(streak_metrics),
            COLORS["red"],
            tr("tooltip.streak"),
            700,
        )
        self.streak_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        set_button_icon(self.streak_button, FIRE_ICON_PATH, 17)
        self.cards_button = make_toolbar_metric_button(
            self._cards_text(cards_metrics), COLORS["yellow"], tr("tooltip.cards")
        )
        self.cards_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        set_button_icon(self.cards_button, BOLT_ICON_PATH, 17)
        self.study_time_button = make_toolbar_metric_button(
            self._study_time_text(study_time_metrics), "#8a8aff", tr("tooltip.study_time"), 650
        )
        self.study_time_button.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        set_button_icon(self.study_time_button, STUDY_TIME_ICON_PATH, 17)
        self.retention_button = make_toolbar_metric_button(
            tr("common.percent", value=format_number(retention_metrics.today_retention)), COLORS["pink"], tr("tooltip.retention"), 650
        )
        set_button_icon(self.retention_button, BRAIN_ICON_PATH, 17)

        for button in [self.experience_button, self.streak_button, self.cards_button, self.study_time_button, self.retention_button]:
            metrics_row.addWidget(button)

        left.addWidget(self.mode_label)
        left.addLayout(metrics_row)
        left.addStretch(1)

        center = QVBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(5)
        self.timer_label = make_clickable_label("25:00", "timer", tr("tooltip.edit_time"))
        self.timer_label.setAlignment(ALIGN_CENTER)
        self.timer_label.setFixedHeight(36)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(144)
        self.progress.setFixedHeight(7)
        self._set_progress_accent(COLORS["red"])
        center.addWidget(self.timer_label, 0, ALIGN_CENTER)
        center.addWidget(self.progress, 0, ALIGN_CENTER)

        right = QHBoxLayout()
        right.setSpacing(0)
        right.setContentsMargins(0, 0, 0, 0)
        timer_controls_row = QHBoxLayout()
        timer_controls_row.setSpacing(12)
        timer_controls_row.setContentsMargins(0, 0, 0, 0)
        utility_controls_row = QHBoxLayout()
        utility_controls_row.setSpacing(12)
        utility_controls_row.setContentsMargins(0, 0, 0, 0)

        self.pause_button = make_pause_button()
        self.stop_button = make_stop_button(COLORS["muted"], 14)
        self.audio_button = make_sound_button(COLORS["muted"], 17)
        self.session_button = QPushButton("")
        self.session_button.setCursor(self.cursor())
        self.session_button.setToolTip(tr("tooltip.session_history"))
        self.session_button.setStyleSheet(
            f"""
            QPushButton {{
                color: #d94b43;
                background: transparent;
                border: 0;
                border-radius: 999px;
                padding: 2px 6px;
                font-size: 14px;
                font-weight: 600;
                line-height: 20px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {COLORS['soft']};
                border-radius: 999px;
            }}
            """
        )
        set_button_icon(self.session_button, HISTORY_ICON_PATH, 17)
        self.feedback_button = make_feedback_button(COLORS["muted"], 16)
        self.settings_button = make_settings_button(COLORS["muted"], 16)

        for button in [self.pause_button, self.stop_button]:
            timer_controls_row.addWidget(button)
        for button in [self.audio_button, self.session_button, self.feedback_button, self.settings_button]:
            utility_controls_row.addWidget(button)

        right.addStretch(1)
        right.addLayout(timer_controls_row)
        right.addSpacing(14)
        right.addLayout(utility_controls_row)

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

    def sync_state(self, state: PomodoroTimerState, study_time_metrics: StudyTimeMetrics | None = None) -> None:
        self.mode_label.setText(mode_label_text(state) if state.mode == MODE_BREAK else self._brand_text())
        self.timer_label.setText(state.time_text)
        self.progress.setValue(int(state.progress * 1000))
        self._set_progress_accent(state.accent)
        set_accent_property(self.mode_label, state.accent)
        set_accent_property(self.timer_label, state.accent)
        set_pause_button_state(self.pause_button, state.paused)
        self.stop_button.setVisible(state.started)
        if study_time_metrics is not None:
            self.study_time_metrics = study_time_metrics
            self.study_time_button.setText(self._study_time_text(study_time_metrics))

    def refresh_metrics(
        self,
        metrics: SessionMetrics,
        experience_metrics: ExperienceMetrics,
        cards_metrics: CardsStudiedMetrics,
        retention_metrics: RetentionMetrics,
        streak_metrics: StreakMetrics,
        study_time_metrics: StudyTimeMetrics,
    ) -> None:
        self.metrics = metrics
        self.experience_metrics = experience_metrics
        self.cards_metrics = cards_metrics
        self.retention_metrics = retention_metrics
        self.streak_metrics = streak_metrics
        self.study_time_metrics = study_time_metrics
        self.session_button.setText("")
        self.experience_button.setText(self._experience_text(experience_metrics))
        self.streak_button.setText(self._streak_text(streak_metrics))
        self.retention_button.setText(tr("common.percent", value=format_number(retention_metrics.today_retention)))
        self.cards_button.setText(self._cards_text(cards_metrics))
        self.study_time_button.setText(self._study_time_text(study_time_metrics))

    def metric_buttons(self) -> Iterable[QPushButton]:
        return [
            self.experience_button,
            self.streak_button,
            self.cards_button,
            self.study_time_button,
            self.retention_button,
            self.session_button,
        ]

    def _experience_text(self, metrics: ExperienceMetrics) -> str:
        return format_number(max(0, metrics.level))

    def _streak_text(self, metrics: StreakMetrics) -> str:
        return format_number(max(0, metrics.days))

    def _cards_text(self, metrics: CardsStudiedMetrics) -> str:
        return format_number(max(0, metrics.cards))

    def _study_time_text(self, metrics: StudyTimeMetrics) -> str:
        return format_study_duration(metrics.today_seconds)

    def _set_progress_accent(self, color: str) -> None:
        self.progress.setStyleSheet(
            f"""
            QProgressBar {{
                background: {COLORS['border']};
                border: 0;
                border-radius: 3px;
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
            """
        )

    def _brand_text(self) -> str:
        return f"<span style='color:{COLORS['text']}'>Pomo</span><span style='color:{COLORS['red']}'>VN</span>"
