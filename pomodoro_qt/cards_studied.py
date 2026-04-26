"""Cards studied metric popover."""

from __future__ import annotations

from .i18n import tr
from .metric_popover import MetricPopover
from .models import SessionMetrics
from .style import COLORS


class CardsStudiedPopover(MetricPopover):
    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__(288)
        self.add_header(
            "\u26a1",
            tr("metric.cards_studied"),
            tr("cards.total", count=metrics.cards),
            tr("cards.subtitle"),
        )
        self.add_stat_grid(tr("metric.new"), str(metrics.new_cards), tr("metric.review"), str(metrics.review_cards))
        self.add_rows(
            [
                (tr("metric.again"), tr("cards.row_value", count=metrics.again_cards)),
                (tr("metric.hard"), tr("cards.row_value", count=metrics.hard_cards)),
                (tr("metric.good"), tr("cards.row_value", count=metrics.good_cards)),
                (tr("metric.easy"), tr("cards.row_value", count=metrics.easy_cards)),
            ]
        )
        self.add_footer(tr("cards.footer_retention", color=COLORS["green"], retention=metrics.retention))


def make_cards_studied_popover(metrics: SessionMetrics) -> CardsStudiedPopover:
    return CardsStudiedPopover(metrics)


__all__ = ["CardsStudiedPopover", "make_cards_studied_popover"]
