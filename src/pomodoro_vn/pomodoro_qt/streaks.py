"""Streak-specific popover widgets for the Pomodoro UI."""

from __future__ import annotations

from aqt.qt import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSize, QVBoxLayout, Qt

from .i18n import format_number, tr
from .popover_shell import PopoverShell, _clear_layout
from .streak_metric import StreakMetrics
from .style import COLORS
from .ui_components import FIRE_ICON_PATH, make_icon_label


ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
POPOVER_WIDTH = 320


class StreakPopover(PopoverShell):
    """Detailed streak popover for the study-streak metric."""

    def __init__(self, metrics: StreakMetrics) -> None:
        super().__init__(POPOVER_WIDTH, margins=(14, 14, 14, 14), spacing=10)
        self.metrics = metrics
        self.refresh_data(metrics)

    def refresh_data(self, metrics: StreakMetrics) -> None:
        self.clear_content()
        self.metrics = metrics
        self._help_sections = _help_sections(metrics)
        self._help_title = tr("help.section_label")
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

    def refresh_metrics(self, metrics: StreakMetrics) -> None:
        self.metrics = metrics
        self.title_label.setText(tr("streak.hero_title", days=format_number(max(0, metrics.days))))
        self.status_label.setText(_status_text(metrics))
        self.cutoff_label.setText(_cutoff_text(metrics))
        self.today_line_label.setText(tr("streak.today_reviews_line", count=format_number(max(0, metrics.today_reviews))))

        self.start_value.setText(metrics.start_date or tr("streak.no_start_date"))
        self.longest_value.setText(tr("metric.days", count=format_number(max(0, metrics.longest_days))))
        self.yesterday_value.setText(tr("streak.review_count", count=format_number(max(0, metrics.yesterday_reviews))))
        self.today_value.setText(tr("streak.review_count", count=format_number(max(0, metrics.today_reviews))))

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

        help_button = QPushButton("?")
        help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        help_button.setFixedSize(QSize(20, 20))
        help_button.setCheckable(True)
        help_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLORS['badge']};
                color: {COLORS['muted']};
                border: 0;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 800;
                padding: 0;
            }}
            QPushButton:hover {{
                background: {COLORS['soft']};
                color: {COLORS['red']};
            }}
            QPushButton:checked {{
                background: {COLORS['red']};
                color: white;
            }}
            """
        )
        help_button.toggled.connect(self._on_help_toggled)
        self._help_button = help_button

        layout.addWidget(icon)
        layout.addLayout(copy, 1)
        layout.addWidget(help_button, 0, Qt.AlignmentFlag.AlignTop)
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

    def _on_help_toggled(self, checked: bool) -> None:
        if checked:
            self._render_help_panel()
        self.set_help_visible(checked)

    def _render_help_panel(self) -> None:
        from .metric_popover import RICH_TEXT
        _clear_layout(self.help_layout)
        if self._help_title:
            title = QLabel(self._help_title)
            title.setStyleSheet(
                f"color: {COLORS['muted']}; font-size: 11px; font-weight: 800; letter-spacing: 1px;"
            )
            self.help_layout.addWidget(title)
            self.help_layout.addSpacing(4)
        for index, (section_title, section_body) in enumerate(self._help_sections):
            heading = QLabel(section_title)
            heading.setStyleSheet("color: #3E3C38; font-size: 13px; font-weight: 700;")
            heading.setWordWrap(True)
            body = QLabel(section_body)
            body.setWordWrap(True)
            body.setTextFormat(RICH_TEXT)
            body.setStyleSheet(
                f"color: {COLORS['text']}; font-size: 11px; font-weight: 500; line-height: 1.45;"
            )
            self.help_layout.addWidget(heading)
            self.help_layout.addSpacing(2)
            self.help_layout.addWidget(body)
            if index < len(self._help_sections) - 1:
                self.help_layout.addSpacing(10)
        self.help_layout.addStretch(1)


def _status_text(metrics: StreakMetrics) -> str:
    if metrics.today_reviews > 0:
        return tr("streak.status_kept")
    return tr("streak.status_need_today")


def _cutoff_text(metrics: StreakMetrics) -> str:
    cutoff_time = tr("streak.cutoff_time", hour=format_number(max(0, metrics.cutoff_hour)))
    if metrics.today_reviews > 0:
        return tr("streak.cutoff_done", time=cutoff_time)
    if metrics.seconds_until_cutoff > 0:
        hours = metrics.seconds_until_cutoff // 3600
        minutes = (metrics.seconds_until_cutoff % 3600) // 60
        return tr("streak.cutoff_remaining", hours=format_number(hours), minutes=format_number(minutes))
    return tr("streak.cutoff_need", time=cutoff_time)


def _help_sections(metrics: StreakMetrics) -> list[tuple[str, str]]:
    return [
        (
            tr("streak.help_what_title"),
            tr("streak.help_what_body", days=format_number(metrics.days)),
        ),
        (
            tr("streak.help_how_title"),
            tr("streak.help_how_body"),
        ),
        (
            tr("streak.help_note_title"),
            tr("streak.help_note_body"),
        ),
    ]


def make_streak_popover(metrics: StreakMetrics) -> StreakPopover:
    return StreakPopover(metrics)


__all__ = ["StreakPopover", "make_streak_popover"]
