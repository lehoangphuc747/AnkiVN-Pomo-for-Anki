"""Sidebar-panel Pomodoro layout."""

from __future__ import annotations

from typing import Iterable

from aqt.qt import QFrame, QHBoxLayout, QPushButton, QVBoxLayout

from .i18n import tr
from .models import PomodoroTimerState, SessionMetrics
from .style import COLORS
from .ui_components import (
    ALIGN_CENTER,
    CircularProgress,
    SYMBOL_FIRE,
    SYMBOL_LIGHTNING,
    SYMBOL_SPARKLE,
    SYMBOL_TOMATO,
    make_audio_mini_button,
    make_button,
    make_label,
    make_session_dots_text,
    make_primary_pause_button,
    make_settings_button,
    make_sidebar_metric_button,
    make_stop_button,
    mode_label_text,
    set_accent_property,
    set_pause_button_state,
)


class SidebarWidget(QFrame):
    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__()
        self.metrics = metrics
        self.setProperty("panel", "sidebar")
        self.setFixedWidth(260)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 32, 24, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.mode_label = make_label(f"{SYMBOL_TOMATO} {tr('mode.pomodoro').upper()}", "caption")
        self.settings_button = make_settings_button(COLORS["muted_light"], 16)
        header.addWidget(self.mode_label)
        header.addStretch(1)
        header.addWidget(self.settings_button)
        root.addLayout(header)
        root.addSpacing(12)

        self.circular = CircularProgress(160, 3, True)
        root.addWidget(self.circular, 0, ALIGN_CENTER)
        root.addSpacing(4)

        self.session_button = self._make_session_button(metrics)
        root.addWidget(self.session_button)
        root.addSpacing(12)

        controls = QHBoxLayout()
        controls.setSpacing(20)
        self.pause_button = make_primary_pause_button()
        self.stop_button = make_stop_button(COLORS["text"], 13)
        controls.addStretch(1)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.stop_button)
        controls.addStretch(1)
        root.addLayout(controls)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {COLORS['border']};")
        root.addWidget(line)

        self.experience_button = make_sidebar_metric_button(
            tr("metric.experience"), self._experience_text(metrics), tr("tooltip.experience")
        )
        self.retention_button = make_sidebar_metric_button(
            tr("metric.retention"), tr("common.percent", value=metrics.retention), tr("tooltip.retention")
        )
        self.cards_button = make_sidebar_metric_button(
            tr("metric.cards_studied"), f"{SYMBOL_LIGHTNING} {tr('metric.cards_short', count=metrics.cards)}", tr("tooltip.cards")
        )
        self.streak_button = make_sidebar_metric_button(
            f"{SYMBOL_FIRE} {tr('metric.streak')}", tr("metric.days", count=metrics.streak_days), tr("tooltip.streak")
        )
        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(0)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        for button in [self.experience_button, self.retention_button, self.cards_button, self.streak_button]:
            metrics_layout.addWidget(button)
        root.addLayout(metrics_layout)

        root.addStretch(1)
        self.audio_button = make_audio_mini_button(tr("audio.title_lofi"))
        root.addWidget(self.audio_button)

    def sync_state(self, state: PomodoroTimerState) -> None:
        self.mode_label.setText(mode_label_text(state))
        self.circular.set_state(state)
        set_accent_property(self.mode_label, state.accent)
        set_pause_button_state(self.pause_button, state.paused, primary=True)
        self.stop_button.setVisible(state.started)

    def refresh_metrics(self, metrics: SessionMetrics) -> None:
        self.metrics = metrics
        self.session_button.setText(self._session_text(metrics))
        self.experience_button.setText(f"{tr('metric.experience'):<14}{self._experience_text(metrics)}")
        self.retention_button.setText(f"{tr('metric.retention'):<14}{tr('common.percent', value=metrics.retention)}")
        self.cards_button.setText(f"{tr('metric.cards_studied'):<14}{SYMBOL_LIGHTNING} {tr('metric.cards_short', count=metrics.cards)}")
        self.streak_button.setText(f"{SYMBOL_FIRE} {tr('metric.streak'):<7}{tr('metric.days', count=metrics.streak_days)}")

    def metric_buttons(self) -> Iterable[QPushButton]:
        return [
            self.session_button,
            self.experience_button,
            self.cards_button,
            self.streak_button,
            self.retention_button,
        ]

    def _make_session_button(self, metrics: SessionMetrics) -> QPushButton:
        button = make_button(self._session_text(metrics), "sessionHistory", tr("tooltip.session_history"))
        button.setStyleSheet(
            f"""
            QPushButton {{
                color: {COLORS['muted']};
                background: transparent;
                border: 0;
                border-radius: 16px;
                padding: 8px 10px;
                font-size: 12px;
                font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{
                background: {COLORS['soft']};
            }}
            """
        )
        return button

    def _session_text(self, metrics: SessionMetrics) -> str:
        return f"{make_session_dots_text(metrics)}\n{tr('session.sidebar', index=metrics.session_index, total=metrics.session_total)}"

    def _experience_text(self, metrics: SessionMetrics) -> str:
        return f"{tr('metric.level_short')} {metrics.level} {metrics.total_xp}/{metrics.next_level_xp} {SYMBOL_SPARKLE}"
