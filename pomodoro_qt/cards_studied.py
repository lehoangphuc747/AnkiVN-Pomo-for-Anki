"""Cards studied metric popover."""

from __future__ import annotations

from aqt.qt import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, Qt

from .i18n import format_number, tr
from .metric_popover import MetricPopover
from .cards_metric import CardsStudiedMetrics
from .style import COLORS
from .ui_components import BOLT_ICON_PATH


ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter


class CardsStudiedPopover(MetricPopover):
    def __init__(self, metrics: CardsStudiedMetrics) -> None:
        super().__init__(320)
        self.refresh_data(metrics)

    def refresh_data(self, metrics: CardsStudiedMetrics) -> None:
        self.clear_content()
        self.add_header(
            "",
            tr("metric.cards_studied"),
            tr("cards.total", count=format_number(metrics.cards)),
            tr("cards.subtitle"),
            COLORS["red"],
            BOLT_ICON_PATH,
            help_sections=_help_sections(metrics),
            help_title=tr("help.section_label"),
        )
        self._add_section_title(tr("cards.section_types"))
        self._add_type_grid(metrics)
        self._add_section_title(tr("cards.section_buttons"))
        self._add_answer_rows(metrics)
        self.add_footer(_footer_text(metrics))

    def _add_section_title(self, text: str) -> None:
        label = QLabel(text)
        label.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {COLORS['text']};")
        label.setToolTip(_section_tooltip(text))
        self.content_layout.addWidget(label)
        self.content_layout.addSpacing(6)

    def _add_type_grid(self, metrics: CardsStudiedMetrics) -> None:
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

    def _add_answer_rows(self, metrics: CardsStudiedMetrics) -> None:
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


def make_cards_studied_popover(metrics: CardsStudiedMetrics) -> CardsStudiedPopover:
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
    tooltip = _type_tooltip(label_text)
    value = QLabel(format_number(max(0, int(count))))
    value.setAlignment(ALIGN_CENTER)
    value.setStyleSheet(f"font-size: 19px; font-weight: 750; color: {accent};")
    value.setToolTip(tooltip)
    label = QLabel(label_text)
    label.setAlignment(ALIGN_CENTER)
    label.setStyleSheet(f"font-size: 10px; font-weight: 750; color: {COLORS['muted']};")
    label.setToolTip(tooltip)
    tile.setToolTip(tooltip)
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
    tooltip = _answer_tooltip(label_text)
    label = QLabel(label_text)
    label.setStyleSheet(f"font-size: 12px; font-weight: 650; color: {COLORS['text']};")
    label.setToolTip(tooltip)
    value = QLabel(tr("cards.row_value", count=format_number(max(0, int(count)))))
    value.setAlignment(ALIGN_RIGHT)
    value.setStyleSheet(f"font-size: 12px; font-weight: 750; color: {accent};")
    value.setToolTip(tooltip)
    row_frame.setToolTip(tooltip)
    row.addWidget(label)
    row.addStretch(1)
    row.addWidget(value)
    return row_frame


def _section_tooltip(text: str) -> str:
    if text == tr("cards.section_types"):
        return tr("cards.section_types_tooltip")
    if text == tr("cards.section_buttons"):
        return tr("cards.section_buttons_tooltip")
    return text


def _type_tooltip(label_text: str) -> str:
    if label_text == tr("metric.review"):
        return tr("cards.review_tooltip")
    if label_text == tr("metric.learning"):
        return tr("cards.learning_tooltip")
    if label_text == tr("metric.relearning"):
        return tr("cards.relearning_tooltip")
    if label_text == tr("metric.filtered"):
        return tr("cards.filtered_tooltip")
    return label_text


def _answer_tooltip(label_text: str) -> str:
    if label_text == tr("metric.again"):
        return tr("cards.again_tooltip")
    if label_text == tr("metric.hard"):
        return tr("cards.hard_tooltip")
    if label_text == tr("metric.good"):
        return tr("cards.good_tooltip")
    if label_text == tr("metric.easy"):
        return tr("cards.easy_tooltip")
    return label_text


def _footer_text(metrics: CardsStudiedMetrics) -> str:
    if metrics.cards <= 0:
        return tr("cards.footer_empty")
    return tr(
        "cards.footer_retention",
        retention=format_number(metrics.retention),
        color=COLORS["green"] if metrics.retention >= 90 else COLORS["red"],
    )


def _help_sections(metrics: CardsStudiedMetrics) -> list[tuple[str, str]]:
    """Build live help text for the popover, citing the user's own numbers."""
    correct = metrics.good_cards + metrics.easy_cards + metrics.hard_cards
    return [
        (
            tr("cards.help_what_title"),
            tr(
                "cards.help_what_body",
                cards=format_number(metrics.cards),
            ),
        ),
        (
            tr("cards.help_how_title"),
            tr(
                "cards.help_how_body",
                review=format_number(metrics.review_cards),
                learning=format_number(metrics.learning_cards),
                relearning=format_number(metrics.relearning_cards),
                filtered=format_number(metrics.filtered_cards),
            ),
        ),
        (
            tr("cards.help_buttons_title"),
            tr(
                "cards.help_buttons_body",
                again=format_number(metrics.again_cards),
                hard=format_number(metrics.hard_cards),
                good=format_number(metrics.good_cards),
                easy=format_number(metrics.easy_cards),
                correct=format_number(correct),
            ),
        ),
        (
            tr("cards.help_note_title"),
            tr("cards.help_note_body"),
        ),
    ]


__all__ = ["CardsStudiedPopover", "make_cards_studied_popover"]
