"""Experience and level metric popover."""

from __future__ import annotations

from .i18n import tr
from .metric_popover import MetricPopover
from .models import SessionMetrics


class ExperiencePopover(MetricPopover):
    def __init__(self, metrics: SessionMetrics) -> None:
        super().__init__(288)
        self.add_header(
            tr("common.xp"),
            tr("metric.experience"),
            f"{tr('metric.level')} {metrics.level}",
            tr("experience.subtitle"),
        )
        self.add_progress(
            metrics.level_progress,
            tr("experience.progress_left", total=metrics.total_xp, next=metrics.next_level_xp),
            tr("experience.to_next_level", xp=metrics.xp_to_next_level, level=metrics.level + 1),
        )
        self.add_rows(
            [
                (tr("metric.again"), tr("experience.ease_rule", count=metrics.again_cards, xp="-1")),
                (tr("metric.hard"), tr("experience.ease_rule", count=metrics.hard_cards, xp="+1")),
                (tr("metric.good"), tr("experience.ease_rule", count=metrics.good_cards, xp="+2")),
                (tr("metric.easy"), tr("experience.ease_rule", count=metrics.easy_cards, xp="+1")),
            ]
        )
        self.add_footer(tr("experience.footer", session_xp=metrics.session_xp, total_xp=metrics.total_xp))


def make_experience_popover(metrics: SessionMetrics) -> ExperiencePopover:
    return ExperiencePopover(metrics)


__all__ = ["ExperiencePopover", "make_experience_popover"]
