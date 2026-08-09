"""Study-time metric popover."""

from __future__ import annotations

from .i18n import format_number, tr
from .metric_popover import MetricPopover
from .study_time_metric import StudyTimeMetrics, format_cutoff_time, format_study_duration, format_study_duration_long
from .style import COLORS
from .ui_components import STUDY_TIME_ICON_PATH


class StudyTimePopover(MetricPopover):
    def __init__(self, metrics: StudyTimeMetrics) -> None:
        super().__init__(320)
        self.refresh_data(metrics)

    def refresh_data(self, metrics: StudyTimeMetrics) -> None:
        self.clear_content()
        self.add_header(
            "",
            tr("metric.study_time"),
            format_study_duration(metrics.today_seconds),
            tr("study_time.subtitle"),
            COLORS["green"],
            STUDY_TIME_ICON_PATH,
            help_sections=_help_sections(metrics),
            help_title=tr("help.section_label"),
        )
        self.add_stat_grid(
            tr("study_time.today_total"),
            format_study_duration(metrics.today_seconds),
            tr("study_time.all_time_total"),
            format_study_duration_long(metrics.all_time_seconds),
        )
        self.add_rows(
            [
                (
                    tr("study_time.today_reviews"),
                    tr("study_time.review_count", count=format_number(max(0, metrics.today_reviews))),
                    COLORS["text"],
                ),
                (
                    tr("study_time.all_time_reviews"),
                    tr("study_time.review_count", count=format_number(max(0, metrics.all_time_reviews))),
                    COLORS["text"],
                ),
                (
                    tr("study_time.reset_label"),
                    tr(
                        "study_time.reset_value",
                        time=format_cutoff_time(metrics.cutoff_seconds),
                        remaining=format_study_duration(metrics.seconds_until_cutoff),
                    ),
                    COLORS["muted"],
                ),
            ]
        )
        self.add_footer(tr("study_time.footer"))


def make_study_time_popover(metrics: StudyTimeMetrics) -> StudyTimePopover:
    return StudyTimePopover(metrics)


def _help_sections(metrics: StudyTimeMetrics) -> list[tuple[str, str]]:
    return [
        (
            tr("study_time.help_what_title"),
            tr("study_time.help_what_body", time=format_study_duration(metrics.today_seconds)),
        ),
        (
            tr("study_time.help_how_title"),
            tr("study_time.help_how_body"),
        ),
        (
            tr("study_time.help_note_title"),
            tr("study_time.help_note_body"),
        ),
    ]


__all__ = ["StudyTimePopover", "make_study_time_popover"]
