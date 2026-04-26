"""Streak-specific popover widgets for the Pomodoro UI."""

from __future__ import annotations

from aqt.qt import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget, Qt

from .i18n import tr
from .models import SessionMetrics
from .popover_shell import PopoverShell
from .style import COLORS


ALIGN_BOTTOM = Qt.AlignmentFlag.AlignBottom
FIRE = "\U0001f525"
SPARKLE = "\u2728"
POPOVER_WIDTH = 272
FOOTER_RADIUS = 12
BAR_RADIUS = 5
CHART_HEIGHT = 76
WEEK_BAR_COUNT = 7


class StreakPopover(PopoverShell):
    """Detailed streak popover matching the mockup's Streaks interaction."""

    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__(POPOVER_WIDTH, margins=(14, 14, 14, 14), spacing=10)
        self.metrics = metrics
        self._bars: list[QFrame] = []

        root = self.content_layout

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        eyebrow = QLabel(f"{FIRE} {tr('streak.eyebrow')}")
        eyebrow.setStyleSheet(
            f"color: {COLORS['red']}; font-size: 11px; font-weight: 800;"
        )
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 650;")
        subtitle = QLabel(tr("streak.subtitle"))
        subtitle.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px;")

        title_box.addWidget(eyebrow)
        title_box.addWidget(self.title_label)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        root.addLayout(header)

        root.addWidget(self._make_week_chart())

        self.today_value = self._make_row(root, tr("metric.today"))
        self.longest_value = self._make_row(root, tr("metric.longest_streak"))
        self.goal_value = self._make_row(root, tr("metric.streak_goal"))

        self.footer_label = QLabel()
        self.footer_label.setWordWrap(True)
        self.footer_label.setStyleSheet(
            f"""
            background: {COLORS['badge']};
            color: {COLORS['muted']};
            border-radius: {FOOTER_RADIUS}px;
            padding: 7px 10px;
            font-size: 11px;
            font-weight: 600;
            """
        )
        root.addWidget(self.footer_label)

        self.refresh_metrics(metrics)

    def refresh_metrics(self, metrics: SessionMetrics) -> None:
        self.metrics = metrics
        self.title_label.setText(tr("metric.days", count=metrics.streak_days))
        self.today_value.setText(f"{tr('streak.today_value', cards=metrics.today_cards, xp=metrics.today_xp)} {SPARKLE}")
        self.longest_value.setText(tr("metric.days", count=metrics.longest_streak_days))
        self.goal_value.setText(tr("metric.study_daily"))
        self.footer_label.setText(tr("streak.footer", days=metrics.streak_days))
        self._sync_chart(metrics)

    def _make_week_chart(self) -> QWidget:
        chart = QWidget()
        chart.setFixedHeight(CHART_HEIGHT)
        layout = QHBoxLayout(chart)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        for _index in range(WEEK_BAR_COUNT):
            bar = QFrame()
            bar.setMouseTracking(True)
            bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._bars.append(bar)
            layout.addWidget(bar, 1, ALIGN_BOTTOM)

        return chart

    def _sync_chart(self, metrics: SessionMetrics) -> None:
        activity = list(metrics.week_activity)[-WEEK_BAR_COUNT:]
        if not activity:
            activity = []
        while len(activity) < WEEK_BAR_COUNT:
            activity.insert(0, None)

        max_cards = max((item.cards for item in activity if item is not None), default=0) or 1

        for index, (bar, item) in enumerate(zip(self._bars, activity)):
            if item is None:
                day = "-"
                cards = 0
                xp = 0
            else:
                day = item.label
                cards = item.cards
                xp = item.xp
            height = max(22, round(CHART_HEIGHT * cards / max_cards))
            color = COLORS["red"] if index == len(activity) - 1 else COLORS["border"]
            bar.setFixedHeight(height)
            bar.setToolTip(tr("streak.tooltip_day", day=day, cards=cards, xp=xp))
            bar.setStyleSheet(f"background: {color}; border: 0; border-radius: {BAR_RADIUS}px;")

    def _make_row(self, root: QVBoxLayout, label_text: str) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(8)

        label = QLabel(label_text)
        label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 12px;")
        value = QLabel()
        value.setStyleSheet("font-size: 12px; font-weight: 650;")

        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(value)
        root.addLayout(row)
        return value


def make_streak_popover(metrics: SessionMetrics) -> StreakPopover:
    return StreakPopover(metrics)


__all__ = ["StreakPopover", "make_streak_popover"]
