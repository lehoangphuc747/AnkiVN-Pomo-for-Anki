"""Retention metric popover."""

from __future__ import annotations

from .i18n import tr
from .metric_popover import MetricPopover
from .models import SessionMetrics
from .style import COLORS
from .ui_components import BRAIN_ICON_PATH


class RetentionPopover(MetricPopover):
    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__(288)
        self.refresh_data(metrics)

    def refresh_data(self, metrics: SessionMetrics) -> None:
        self.clear_content()
        correct_cards = metrics.good_cards + metrics.easy_cards + metrics.hard_cards
        self.add_header(
            "",
            tr("metric.retention"),
            tr("common.percent", value=metrics.retention),
            tr("retention.subtitle"),
            COLORS["green"],
            BRAIN_ICON_PATH,
        )
        self.add_progress(
            metrics.retention,
            tr("retention.correct_count", count=correct_cards),
            tr("retention.again_count", count=metrics.again_cards),
            COLORS["green"],
        )
        self.add_rows(
            [
                (tr("metric.good_easy"), tr("retention.row_cards", count=metrics.good_cards + metrics.easy_cards), COLORS["green"]),
                (tr("metric.hard"), tr("retention.row_cards", count=metrics.hard_cards)),
                (tr("metric.again"), tr("retention.row_cards", count=metrics.again_cards), COLORS["red"]),
            ]
        )
        self.add_footer(_footer_text(metrics))


def make_retention_popover(metrics: SessionMetrics) -> RetentionPopover:
    return RetentionPopover(metrics)


def _footer_text(metrics: SessionMetrics) -> str:
    if metrics.cards <= 0:
        return tr("retention.footer_empty")
    if metrics.retention >= 90:
        return tr("retention.footer_stable")
    return tr("retention.footer_active")


__all__ = ["RetentionPopover", "make_retention_popover"]
