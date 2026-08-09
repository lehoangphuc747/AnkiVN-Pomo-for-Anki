"""Experience and level metric popover."""

from __future__ import annotations

from aqt.qt import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QSize, QVBoxLayout, Qt

from .i18n import format_number, tr
from .metric_popover import MetricPopover
from .experience_metric import ExperienceMetrics
from .style import COLORS
from .popover_shell import _clear_layout


ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight


class ExperiencePopover(MetricPopover):
    def __init__(self, metrics: ExperienceMetrics) -> None:
        super().__init__(320)
        self.refresh_data(metrics)

    def refresh_data(self, metrics: ExperienceMetrics) -> None:
        self.clear_content()
        self._help_sections = _help_sections(metrics)
        self._help_title = tr("help.section_label")
        self._add_hero(metrics)
        self._add_progress_card(metrics)
        self._add_breakdown(metrics)

    def _add_hero(self, metrics: ExperienceMetrics) -> None:
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

        badge = QLabel(format_number(metrics.level))
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
        title = QLabel(
            f"{tr('metric.level')} {format_number(metrics.level)} · "
            f"{format_number(metrics.experience)} {tr('common.xp')}"
        )
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 18px; font-weight: 700;")
        subtitle = QLabel(
            tr(
                "experience.to_next_level",
                xp=format_number(metrics.experience_to_next_level),
                level=format_number(metrics.level + 1),
            )
        )
        subtitle.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px; font-weight: 600;")
        copy.addWidget(eyebrow)
        copy.addWidget(title)
        copy.addWidget(subtitle)

        layout.addWidget(badge)
        layout.addLayout(copy, 1)
        layout.addWidget(help_button, 0, Qt.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(hero)
        self.content_layout.addSpacing(12)

    def _add_progress_card(self, metrics: ExperienceMetrics) -> None:
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
        value = QLabel(tr("common.percent", value=format_number(metrics.level_progress)))
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

        detail = QLabel(
            tr(
                "experience.progress_left",
                total=format_number(metrics.experience),
                next=format_number(metrics.next_level_experience),
            )
        )
        detail.setStyleSheet(f"color: {COLORS['muted_light']}; font-size: 10px; font-weight: 650;")

        layout.addLayout(row)
        layout.addWidget(bar)
        layout.addWidget(detail)
        self.content_layout.addWidget(card)
        self.content_layout.addSpacing(12)

    def _add_breakdown(self, metrics: ExperienceMetrics) -> None:
        title = QLabel(tr("experience.breakdown"))
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 700;")
        self.content_layout.addWidget(title)
        self.content_layout.addSpacing(4)
        rows = QVBoxLayout()
        rows.setContentsMargins(0, 0, 0, 0)
        rows.setSpacing(8)
        for label, count in [
            (tr("metric.again"), metrics.again_cards),
            (tr("metric.hard"), metrics.hard_cards),
            (tr("metric.good"), metrics.good_cards),
            (tr("metric.easy"), metrics.easy_cards),
        ]:
            rows.addWidget(self._breakdown_row(label, count))
        self.content_layout.addLayout(rows)

    def _breakdown_row(self, label_text: str, count: int) -> QFrame:
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
        count_label = QLabel(tr("experience.cards_count", count=format_number(count)))
        count_label.setAlignment(ALIGN_RIGHT)
        count_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px; font-weight: 600;")

        layout.addWidget(label, 1)
        layout.addWidget(count_label)
        return row

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


def make_experience_popover(metrics: ExperienceMetrics) -> ExperiencePopover:
    return ExperiencePopover(metrics)


def _help_sections(metrics: ExperienceMetrics) -> list[tuple[str, str]]:
    return [
        (
            tr("experience.help_what_title"),
            tr(
                "experience.help_what_body",
                xp=format_number(metrics.experience),
                level=format_number(metrics.level),
            ),
        ),
        (
            tr("experience.help_how_title"),
            tr("experience.help_how_body"),
        ),
        (
            tr("experience.help_note_title"),
            tr("experience.help_note_body"),
        ),
    ]


__all__ = ["ExperiencePopover", "make_experience_popover"]
