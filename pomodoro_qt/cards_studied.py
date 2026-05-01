"""Cards studied metric popover."""

from __future__ import annotations

from aqt.qt import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, Qt

from .i18n import tr
from .metric_popover import MetricPopover
from .models import SessionMetrics
from .style import COLORS
from .ui_components import BOLT_ICON_PATH


ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter


class CardsStudiedPopover(MetricPopover):
    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__(320)
        self.refresh_data(metrics)

    def refresh_data(self, metrics: SessionMetrics) -> None:
        self.clear_content()
        self.add_header(
            "",
            tr("metric.cards_studied"),
            tr("cards.total", count=metrics.cards),
            tr("cards.subtitle"),
            COLORS["red"],
            BOLT_ICON_PATH,
        )
        self._add_section_title(tr("cards.section_types"))
        self._add_type_grid(metrics)
        self._add_section_title(tr("cards.section_buttons"))
        self._add_answer_rows(metrics)
        self.add_footer(_footer_text(metrics))

    def _add_section_title(self, text: str) -> None:
        label = QLabel(text)
        label.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {COLORS['text']};")
        self.content_layout.addWidget(label)
        self.content_layout.addSpacing(6)

    def _add_type_grid(self, metrics: SessionMetrics) -> None:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.addWidget(_type_tile(tr("metric.review"), metrics.review_cards, COLORS["red"]), 0, 0)
        grid.addWidget(_type_tile(tr("metric.learning"), metrics.learning_cards, COLORS["text"]), 0, 1)
        grid.addWidget(_type_tile(tr("metric.relearning"), metrics.relearning_cards, COLORS["red_dark"]), 1, 0)
        grid.addWidget(_type_tile(tr("metric.filtered"), metrics.filtered_cards, COLORS["muted"]), 1, 1)
        self.content_layout.addLayout(grid)
        self.content_layout.addSpacing(14)

    def _add_answer_rows(self, metrics: SessionMetrics) -> None:
        rows = QVBoxLayout()
        rows.setContentsMargins(0, 0, 0, 0)
        rows.setSpacing(8)
        for label, count, color in [
            (tr("metric.again"), metrics.again_cards, COLORS["red"]),
            (tr("metric.hard"), metrics.hard_cards, COLORS["text"]),
            (tr("metric.good"), metrics.good_cards, COLORS["green"]),
            (tr("metric.easy"), metrics.easy_cards, COLORS["green"]),
        ]:
            rows.addWidget(_answer_row(label, count, color))
        self.content_layout.addLayout(rows)


def make_cards_studied_popover(metrics: SessionMetrics) -> CardsStudiedPopover:
    return CardsStudiedPopover(metrics)


def _type_tile(label_text: str, count: int, accent: str) -> QFrame:
    tile = QFrame()
    tile.setStyleSheet(
        f"""
        QFrame {{
            background: #FAF9F6;
            border: 0;
            border-radius: 10px;
        }}
        """
    )
    layout = QVBoxLayout(tile)
    layout.setContentsMargins(10, 9, 10, 9)
    layout.setSpacing(3)
    value = QLabel(str(max(0, int(count))))
    value.setAlignment(ALIGN_CENTER)
    value.setStyleSheet(f"font-size: 19px; font-weight: 750; color: {accent};")
    label = QLabel(label_text)
    label.setAlignment(ALIGN_CENTER)
    label.setStyleSheet(f"font-size: 10px; font-weight: 750; color: {COLORS['muted']};")
    layout.addWidget(value)
    layout.addWidget(label)
    return tile


def _answer_row(label_text: str, count: int, accent: str) -> QFrame:
    row_frame = QFrame()
    row_frame.setStyleSheet(
        f"""
        QFrame {{
            background: #FAF9F6;
            border: 0;
            border-radius: 8px;
        }}
        """
    )
    row = QHBoxLayout(row_frame)
    row.setContentsMargins(10, 7, 10, 7)
    row.setSpacing(8)
    label = QLabel(label_text)
    label.setStyleSheet(f"font-size: 12px; font-weight: 650; color: {COLORS['text']};")
    value = QLabel(tr("cards.row_value", count=max(0, int(count))))
    value.setAlignment(ALIGN_RIGHT)
    value.setStyleSheet(f"font-size: 12px; font-weight: 750; color: {accent};")
    row.addWidget(label)
    row.addStretch(1)
    row.addWidget(value)
    return row_frame


def _footer_text(metrics: SessionMetrics) -> str:
    if metrics.cards <= 0:
        return tr("cards.footer_empty")
    return tr(
        "cards.footer_retention",
        retention=metrics.retention,
        color=COLORS["green"] if metrics.retention >= 90 else COLORS["red"],
    )


__all__ = ["CardsStudiedPopover", "make_cards_studied_popover"]
