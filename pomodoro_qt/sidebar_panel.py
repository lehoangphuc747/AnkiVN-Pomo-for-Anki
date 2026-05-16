"""Sidebar-panel Pomodoro layout."""

from __future__ import annotations

from typing import Iterable

from aqt.qt import QFrame, QHBoxLayout, QPushButton, QVBoxLayout

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
    CircularProgress,
    BOLT_ICON_PATH,
    GROWTH_ICON_PATH,
    HISTORY_ICON_PATH,
    SYMBOL_LIGHTNING,
    TOMATO_ICON_PATH,
    FIRE_ICON_PATH,
    STUDY_TIME_ICON_PATH,
    make_audio_mini_button,
    make_button,
    make_feedback_button,
    make_icon_text_label,
    make_primary_pause_button,
    make_settings_button,
    make_sidebar_metric_button,
    make_stop_button,
    mode_label_text,
    set_button_icon,
    set_accent_property,
    set_pause_button_state,
)


class SidebarWidget(QFrame):
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
        self.setProperty("panel", "sidebar")
        self.setFixedWidth(260)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 32, 24, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(10)
        self.mode_label = make_icon_text_label(
            TOMATO_ICON_PATH,
            self._brand_text(),
            "brand",
            18,
            7,
        )
        self.feedback_button = make_feedback_button(COLORS["muted_light"], 16)
        self.settings_button = make_settings_button(COLORS["muted_light"], 16)
        header.addWidget(self.mode_label)
        header.addStretch(1)
        header.addWidget(self.feedback_button)
        header.addWidget(self.settings_button)
        root.addLayout(header)
        root.addSpacing(12)

        self.circular = CircularProgress(160, 3, True)
        root.addWidget(self.circular, 0, ALIGN_CENTER)
        root.addSpacing(4)

        controls = QHBoxLayout()
        controls.setSpacing(14)
        self.pause_button = make_primary_pause_button()
        self.stop_button = make_stop_button(COLORS["text"], 13)
        self.session_button = self._make_session_button(metrics)
        controls.addStretch(1)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.session_button)
        controls.addStretch(1)
        root.addLayout(controls)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {COLORS['border']};")
        root.addWidget(line)

        self.experience_button = make_sidebar_metric_button(
            tr("metric.experience"), self._experience_text(experience_metrics), tr("tooltip.experience"), COLORS["yellow"], GROWTH_ICON_PATH
        )
        self.retention_button = make_sidebar_metric_button(
            tr("metric.retention"),
            tr("common.percent", value=format_number(retention_metrics.today_retention)),
            tr("tooltip.retention"),
            COLORS["pink"],
            BRAIN_ICON_PATH,
        )
        self.cards_button = make_sidebar_metric_button(
            tr("metric.cards_studied"),
            tr("metric.cards_short", count=format_number(cards_metrics.cards)),
            tr("tooltip.cards"),
            COLORS["yellow"],
            BOLT_ICON_PATH,
        )
        self.study_time_button = make_sidebar_metric_button(
            tr("metric.study_time"),
            format_study_duration(study_time_metrics.today_seconds),
            tr("tooltip.study_time"),
            COLORS["green"],
            STUDY_TIME_ICON_PATH,
        )
        self.streak_button = make_sidebar_metric_button(
            tr("metric.streak"), tr("metric.days", count=format_number(streak_metrics.days)), tr("tooltip.streak"), COLORS["red"], FIRE_ICON_PATH
        )
        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(0)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        for button in [self.experience_button, self.streak_button, self.cards_button, self.study_time_button, self.retention_button]:
            metrics_layout.addWidget(button)
        root.addLayout(metrics_layout)

        root.addStretch(1)
        self.audio_button = make_audio_mini_button(tr("audio.short_rain"))
        root.addWidget(self.audio_button)

    def sync_state(self, state: PomodoroTimerState, study_time_metrics: StudyTimeMetrics | None = None) -> None:
        self.mode_label.setText(mode_label_text(state) if state.mode == MODE_BREAK else self._brand_text())
        self.circular.set_state(state)
        set_accent_property(self.mode_label, state.accent)
        set_pause_button_state(self.pause_button, state.paused, primary=True)
        self.stop_button.setVisible(state.started)
        if study_time_metrics is not None:
            self.study_time_metrics = study_time_metrics
            self.study_time_button.set_value(format_study_duration(study_time_metrics.today_seconds))

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
        self.session_button.setText(self._session_text(metrics))
        self.experience_button.set_value(self._experience_text(experience_metrics))
        self.retention_button.set_value(tr("common.percent", value=format_number(retention_metrics.today_retention)))
        self.cards_button.set_value(tr("metric.cards_short", count=format_number(cards_metrics.cards)))
        self.study_time_button.set_value(format_study_duration(study_time_metrics.today_seconds))
        self.streak_button.set_value(tr("metric.days", count=format_number(streak_metrics.days)))

    def metric_buttons(self) -> Iterable[QPushButton]:
        return [
            self.session_button,
            self.experience_button,
            self.cards_button,
            self.study_time_button,
            self.streak_button,
            self.retention_button,
        ]

    def _make_session_button(self, metrics: SessionMetrics) -> QPushButton:
        button = make_button(self._session_text(metrics), "sessionHistory", tr("tooltip.session_history"))
        set_button_icon(button, HISTORY_ICON_PATH, 14)
        button.setFixedSize(36, 36)
        button.setStyleSheet(
            f"""
            QPushButton {{
                color: {COLORS['muted']};
                background: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 0;
                font-size: 12px;
                font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{
                background: {COLORS['soft']};
                border: 1px solid {COLORS['border']};
            }}
            """
        )
        return button

    def _session_text(self, metrics: SessionMetrics) -> str:
        return ""

    def _experience_text(self, metrics: ExperienceMetrics) -> str:
        return f"{tr('metric.level_short')} {format_number(max(0, metrics.level))}"

    def _brand_text(self) -> str:
        return f"<span style='color:{COLORS['text']}'>Pomo</span><span style='color:{COLORS['red']}'>VN</span>"
