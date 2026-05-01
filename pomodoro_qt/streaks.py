"""Streak-specific popover widgets for the Pomodoro UI."""

from __future__ import annotations

from aqt.qt import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, Qt

from .i18n import tr
from .models import SessionMetrics
from .popover_shell import PopoverShell
from .style import COLORS
from .ui_components import FIRE_ICON_PATH, make_icon_label


ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
POPOVER_WIDTH = 320


class StreakPopover(PopoverShell):
    """Detailed streak popover for the study-streak metric."""

    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__(POPOVER_WIDTH, margins=(14, 14, 14, 14), spacing=10)
        self.metrics = metrics
        self.refresh_data(metrics)

    def refresh_data(self, metrics: SessionMetrics) -> None:
        self.clear_content()
        self.metrics = metrics
        root = self.content_layout

        self.title_label = QLabel()
        self.status_label = QLabel()
        self.cutoff_label = QLabel()
        root.addWidget(self._make_hero())

        self.today_line_label = QLabel()
        root.addWidget(self._make_today_line())

        self.start_value = QLabel()
        self.longest_value = QLabel()
        self.yesterday_value = QLabel()
        self.today_value = QLabel()
        root.addLayout(self._make_context_grid())

        self.refresh_metrics(metrics)

    def refresh_metrics(self, metrics: SessionMetrics) -> None:
        self.metrics = metrics
        self.title_label.setText(tr("streak.hero_title", days=max(0, metrics.streak_days)))
        self.status_label.setText(_status_text(metrics))
        self.cutoff_label.setText(_cutoff_text(metrics))
        self.today_line_label.setText(tr("streak.today_reviews_line", count=max(0, metrics.today_reviews)))

        self.start_value.setText(metrics.streak_start_date or tr("streak.no_start_date"))
        self.longest_value.setText(tr("metric.days", count=max(0, metrics.longest_streak_days)))
        self.yesterday_value.setText(tr("streak.review_count", count=max(0, metrics.yesterday_reviews)))
        self.today_value.setText(tr("streak.review_count", count=max(0, metrics.today_reviews)))

    def _make_hero(self) -> QFrame:
        hero = QFrame()
        hero.setStyleSheet(
            f"""
            QFrame {{
                background: {COLORS['red_light']};
                border: 0;
                border-radius: 14px;
            }}
            """
        )
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(13, 12, 13, 12)
        layout.setSpacing(11)

        icon = QFrame()
        icon.setFixedSize(36, 36)
        icon.setStyleSheet(
            """
            QFrame {
                background: #FFFFFF;
                border: 0;
                border-radius: 18px;
            }
            """
        )
        icon_layout = QVBoxLayout(icon)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(make_icon_label(FIRE_ICON_PATH, 22), 0, ALIGN_CENTER)

        copy = QVBoxLayout()
        copy.setContentsMargins(0, 0, 0, 0)
        copy.setSpacing(3)
        eyebrow = QLabel(tr("streak.eyebrow"))
        eyebrow.setStyleSheet(f"color: {COLORS['red']}; font-size: 10px; font-weight: 800; letter-spacing: 1px;")
        self.title_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 21px; font-weight: 760;")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 700;")
        self.cutoff_label.setWordWrap(True)
        self.cutoff_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px; font-weight: 650;")
        copy.addWidget(eyebrow)
        copy.addWidget(self.title_label)
        copy.addWidget(self.status_label)
        copy.addWidget(self.cutoff_label)

        layout.addWidget(icon)
        layout.addLayout(copy, 1)
        return hero

    def _make_today_line(self) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            """
            QFrame {
                background: #FAF9F6;
                border: 0;
                border-radius: 10px;
            }
            """
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(11, 8, 11, 8)
        self.today_line_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 700;")
        layout.addWidget(self.today_line_label)
        return row

    def _make_context_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.addWidget(self._make_stat_tile(tr("streak.start_date"), self.start_value), 0, 0)
        grid.addWidget(self._make_stat_tile(tr("metric.longest_streak"), self.longest_value), 0, 1)
        grid.addWidget(self._make_stat_tile(tr("streak.yesterday"), self.yesterday_value), 1, 0)
        grid.addWidget(self._make_stat_tile(tr("metric.today"), self.today_value), 1, 1)
        return grid

    def _make_stat_tile(self, label_text: str, value: QLabel) -> QFrame:
        tile = QFrame()
        tile.setStyleSheet(
            """
            QFrame {
                background: #FAF9F6;
                border: 0;
                border-radius: 10px;
            }
            """
        )
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 10px; font-weight: 800;")
        value.setWordWrap(True)
        value.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 720;")
        layout.addWidget(label)
        layout.addWidget(value)
        return tile


def _status_text(metrics: SessionMetrics) -> str:
    if metrics.today_reviews > 0:
        return tr("streak.status_kept")
    return tr("streak.status_need_today")


def _cutoff_text(metrics: SessionMetrics) -> str:
    cutoff_time = tr("streak.cutoff_time", hour=max(0, metrics.cutoff_hour))
    if metrics.today_reviews > 0:
        return tr("streak.cutoff_done", time=cutoff_time)
    if metrics.seconds_until_cutoff > 0:
        hours = metrics.seconds_until_cutoff // 3600
        minutes = (metrics.seconds_until_cutoff % 3600) // 60
        return tr("streak.cutoff_remaining", hours=hours, minutes=minutes)
    return tr("streak.cutoff_need", time=cutoff_time)


def make_streak_popover(metrics: SessionMetrics) -> StreakPopover:
    return StreakPopover(metrics)


__all__ = ["StreakPopover", "make_streak_popover"]
