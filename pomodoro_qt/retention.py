"""Retention metric popover."""

from __future__ import annotations

from .i18n import format_number, tr
from .metric_popover import MetricPopover
from .retention_metric import RetentionMetrics
from .style import COLORS
from .ui_components import BRAIN_ICON_PATH


class RetentionPopover(MetricPopover):
    def __init__(self, metrics: RetentionMetrics) -> None:
        super().__init__(288)
        self.refresh_data(metrics)

    def refresh_data(self, metrics: RetentionMetrics) -> None:
        self.clear_content()
        correct_cards = metrics.good_cards + metrics.easy_cards + metrics.hard_cards
        self.add_header(
            "",
            tr("metric.retention"),
            tr("common.percent", value=format_number(metrics.today_retention)),
            tr("retention.subtitle"),
            COLORS["green"],
            BRAIN_ICON_PATH,
        )
        self.add_progress(
            metrics.today_retention,
            tr("retention.correct_count", count=format_number(correct_cards)),
            tr("retention.again_count", count=format_number(metrics.again_cards)),
            COLORS["green"],
        )
        self.add_stat_grid(
            tr("metric.today"),
            tr("common.percent", value=format_number(metrics.today_retention)),
            tr("metric.all_time_retention"),
            tr("common.percent", value=format_number(metrics.all_time_retention)),
        )
        self.add_rows(
            [
                (
                    tr("metric.good_easy"),
                    tr("retention.row_cards", count=format_number(metrics.good_cards + metrics.easy_cards)),
                    COLORS["green"],
                ),
                (tr("metric.hard"), tr("retention.row_cards", count=format_number(metrics.hard_cards))),
                (tr("metric.again"), tr("retention.row_cards", count=format_number(metrics.again_cards)), COLORS["red"]),
                (tr("retention.all_time_reviews"), tr("retention.row_cards", count=format_number(metrics.all_time_cards)), COLORS["text"]),
            ]
        )
        self.add_footer(_footer_text(metrics))


def make_retention_popover(metrics: RetentionMetrics) -> RetentionPopover:
    return RetentionPopover(metrics)


def _footer_text(metrics: RetentionMetrics) -> str:
    if metrics.today_cards <= 0:
        return tr("retention.footer_empty")
    if metrics.today_retention >= 90:
        return tr("retention.footer_stable")
    return tr("retention.footer_active")


__all__ = ["RetentionPopover", "make_retention_popover"]
