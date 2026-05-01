"""Experience and level metric popover."""

from __future__ import annotations

from aqt.qt import QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, Qt

from .i18n import tr
from .metric_popover import MetricPopover
from .models import SessionMetrics
from .style import COLORS


ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight


class ExperiencePopover(MetricPopover):
    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__(320)
        self.refresh_data(metrics)

    def refresh_data(self, metrics: SessionMetrics) -> None:
        self.clear_content()
        self._add_hero(metrics)
        self._add_progress_card(metrics)
        self._add_stats(metrics)
        self._add_breakdown(metrics)

    def _add_hero(self, metrics: SessionMetrics) -> None:
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
        layout.setContentsMargins(14, 13, 14, 13)
        layout.setSpacing(12)

        badge = QLabel(str(metrics.level))
        badge.setAlignment(ALIGN_CENTER)
        badge.setFixedSize(48, 48)
        badge.setStyleSheet(
            f"""
            background: {COLORS['red']};
            color: white;
            border-radius: 24px;
            font-size: 20px;
            font-weight: 750;
            """
        )

        copy = QVBoxLayout()
        copy.setContentsMargins(0, 0, 0, 0)
        copy.setSpacing(3)
        eyebrow = QLabel(tr("metric.experience").upper())
        eyebrow.setStyleSheet(
            f"color: {COLORS['red']}; font-size: 10px; font-weight: 800; letter-spacing: 1px;"
        )
        title = QLabel(f"{tr('metric.level')} {metrics.level}")
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 18px; font-weight: 700;")
        subtitle = QLabel(tr("experience.to_next_level", xp=metrics.xp_to_next_level, level=metrics.level + 1))
        subtitle.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px; font-weight: 600;")
        copy.addWidget(eyebrow)
        copy.addWidget(title)
        copy.addWidget(subtitle)

        layout.addWidget(badge)
        layout.addLayout(copy, 1)
        self.content_layout.addWidget(hero)
        self.content_layout.addSpacing(12)

    def _add_progress_card(self, metrics: SessionMetrics) -> None:
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background: #FAF9F6;
                border: 0;
                border-radius: 12px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 11, 12, 11)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        title = QLabel(tr("experience.total_progress"))
        value = QLabel(f"{metrics.level_progress}%")
        value.setAlignment(ALIGN_RIGHT)
        title.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px; font-weight: 700;")
        value.setStyleSheet(f"color: {COLORS['red']}; font-size: 12px; font-weight: 800;")
        row.addWidget(title)
        row.addStretch(1)
        row.addWidget(value)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(max(0, min(100, metrics.level_progress)))
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: #EEECE6;
                border: 0;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['red']};
                border-radius: 4px;
            }}
            """
        )

        detail = QLabel(tr("experience.progress_left", total=metrics.total_xp, next=metrics.next_level_xp))
        detail.setStyleSheet(f"color: {COLORS['muted_light']}; font-size: 10px; font-weight: 650;")

        layout.addLayout(row)
        layout.addWidget(bar)
        layout.addWidget(detail)
        self.content_layout.addWidget(card)
        self.content_layout.addSpacing(12)

    def _add_stats(self, metrics: SessionMetrics) -> None:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.addWidget(self._stat_tile(tr("metric.session_xp"), f"+{metrics.session_xp} {tr('common.xp')}"), 0, 0)
        grid.addWidget(self._stat_tile(tr("metric.total_xp"), f"{metrics.total_xp} {tr('common.xp')}"), 0, 1)
        self.content_layout.addLayout(grid)
        self.content_layout.addSpacing(14)

    def _add_breakdown(self, metrics: SessionMetrics) -> None:
        title = QLabel(tr("experience.breakdown"))
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 700;")
        self.content_layout.addWidget(title)
        self.content_layout.addSpacing(4)
        rows = QVBoxLayout()
        rows.setContentsMargins(0, 0, 0, 0)
        rows.setSpacing(8)
        for label, count, xp, color in [
            (tr("metric.again"), metrics.again_cards, "-1", COLORS["muted"]),
            (tr("metric.hard"), metrics.hard_cards, "+1", COLORS["green"]),
            (tr("metric.good"), metrics.good_cards, "+2", COLORS["red"]),
            (tr("metric.easy"), metrics.easy_cards, "+1", COLORS["green"]),
        ]:
            rows.addWidget(self._breakdown_row(label, count, xp, color))
        self.content_layout.addLayout(rows)

    def _breakdown_row(self, label_text: str, count: int, xp_text: str, color: str) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            f"""
            QFrame {{
                background: #FAF9F6;
                border: 0;
                border-radius: 10px;
            }}
            """
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 650;")
        count_label = QLabel(tr("experience.cards_count", count=count))
        count_label.setAlignment(ALIGN_RIGHT)
        count_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px; font-weight: 600;")
        xp_badge = QLabel(tr("experience.xp_per_card", xp=xp_text))
        xp_badge.setAlignment(ALIGN_CENTER)
        xp_badge.setStyleSheet(
            f"""
            background: #FFFFFF;
            color: {color};
            border: 0;
            border-radius: 8px;
            padding: 3px 7px;
            font-size: 11px;
            font-weight: 750;
            """
        )

        layout.addWidget(label, 1)
        layout.addWidget(count_label)
        layout.addWidget(xp_badge)
        return row

    def _stat_tile(self, label_text: str, value_text: str) -> QFrame:
        tile = QFrame()
        tile.setStyleSheet(
            f"""
            QFrame {{
                background: #FFFFFF;
                border: 0;
                border-radius: 12px;
            }}
            """
        )
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 10px; font-weight: 800;")
        value = QLabel(value_text)
        value.setStyleSheet(f"color: {COLORS['text']}; font-size: 15px; font-weight: 700;")
        layout.addWidget(label)
        layout.addWidget(value)
        return tile


def make_experience_popover(metrics: SessionMetrics) -> ExperiencePopover:
    return ExperiencePopover(metrics)


__all__ = ["ExperiencePopover", "make_experience_popover"]
