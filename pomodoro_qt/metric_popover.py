"""Shared builders for metric popovers that mirror the HTML mockup."""

from __future__ import annotations

from aqt.qt import QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, Qt

from .i18n import tr
from .popover_shell import PopoverShell
from .style import COLORS


ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
ALIGN_RIGHT = Qt.AlignmentFlag.AlignRight
RICH_TEXT = Qt.TextFormat.RichText


class MetricPopover(PopoverShell):
    def __init__(self, width: int = 288) -> None:
        super().__init__(width, spacing=0)

    def add_header(self, icon: str, eyebrow: str, title: str, subtitle: str, accent: str = COLORS["red"]) -> None:
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(2)

        eyebrow_row = QHBoxLayout()
        eyebrow_row.setContentsMargins(0, 0, 0, 0)
        eyebrow_row.setSpacing(6)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {accent}; font-size: 13px; font-weight: 800;")
        eyebrow_label = QLabel(eyebrow)
        eyebrow_label.setStyleSheet(
            f"color: {accent}; font-size: 11px; font-weight: 800; letter-spacing: 1px;"
        )
        eyebrow_row.addWidget(icon_label)
        eyebrow_row.addWidget(eyebrow_label)
        eyebrow_row.addStretch(1)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: 650; color: #3E3C38;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(f"font-size: 11px; color: {COLORS['muted']};")

        title_box.addLayout(eyebrow_row)
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)

        close_button = QPushButton("×")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setFixedSize(22, 22)
        close_button.setToolTip(tr("common.close"))
        close_button.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: 0;
                color: {COLORS['muted_light']};
                font-size: 17px;
                font-weight: 600;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {COLORS['red']};
                background: transparent;
            }}
            """
        )
        close_button.clicked.connect(self.hide)

        header.addLayout(title_box, 1)
        header.addWidget(close_button, 0, Qt.AlignmentFlag.AlignTop)
        self.content_layout.addLayout(header)
        self.content_layout.addSpacing(14)

    def add_progress(self, value: int, left_text: str, right_text: str, accent: str = COLORS["red"]) -> None:
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(max(0, min(100, value)))
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: {COLORS['border']};
                border: 0;
                border-radius: 3px;
                height: 6px;
            }}
            QProgressBar::chunk {{
                background: {accent};
                border-radius: 3px;
            }}
            """
        )

        labels = QHBoxLayout()
        labels.setContentsMargins(0, 0, 0, 0)
        left = QLabel(left_text)
        right = QLabel(right_text)
        for label in (left, right):
            label.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {COLORS['muted']};")
        labels.addWidget(left)
        labels.addStretch(1)
        labels.addWidget(right)

        self.content_layout.addWidget(bar)
        self.content_layout.addSpacing(6)
        self.content_layout.addLayout(labels)
        self.content_layout.addSpacing(16)

    def add_rows(self, rows: list[tuple[str, ...]]) -> None:
        rows_box = QVBoxLayout()
        rows_box.setContentsMargins(0, 0, 0, 0)
        rows_box.setSpacing(10)
        for row_data in rows:
            if len(row_data) == 2:
                label_text, value_text = row_data
                value_color = COLORS["text"]
            else:
                label_text, value_text, value_color = row_data
            rows_box.addLayout(self._make_row(label_text, value_text, value_color))
        self.content_layout.addLayout(rows_box)

    def add_footer(self, text: str) -> None:
        footer = QLabel(text)
        footer.setWordWrap(True)
        footer.setTextFormat(RICH_TEXT)
        footer.setStyleSheet(
            f"""
            background: {COLORS['badge']};
            color: {COLORS['muted']};
            border-radius: 12px;
            padding: 8px 12px;
            font-size: 11px;
            font-weight: 600;
            """
        )
        self.content_layout.addSpacing(16)
        self.content_layout.addWidget(footer)

    def add_stat_grid(self, first_label: str, first_value: str, second_label: str, second_value: str) -> None:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.addWidget(self._stat_tile(first_label, first_value), 0, 0)
        grid.addWidget(self._stat_tile(second_label, second_value), 0, 1)
        self.content_layout.addLayout(grid)
        self.content_layout.addSpacing(16)

    def add_timeline_item(
        self,
        marker: str,
        title: str,
        time_text: str,
        detail: str,
        color: str,
        is_last: bool = False,
    ) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        marker_box = QVBoxLayout()
        marker_box.setContentsMargins(0, 0, 0, 0)
        marker_box.setSpacing(4)
        circle = QLabel(marker)
        circle.setFixedSize(24, 24)
        circle.setAlignment(ALIGN_CENTER)
        circle.setStyleSheet(
            f"""
            background: {color};
            color: white;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 800;
            """
        )
        marker_box.addWidget(circle, 0, ALIGN_CENTER)
        if not is_last:
            connector = QFrame()
            connector.setFixedWidth(1)
            connector.setMinimumHeight(26)
            connector.setStyleSheet(f"background: {COLORS['border']}; border: 0;")
            marker_box.addWidget(connector, 1, ALIGN_CENTER)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 650; color: #3E3C38;")
        time_label = QLabel(time_text)
        time_label.setAlignment(ALIGN_RIGHT)
        time_label.setStyleSheet(f"font-size: 11px; font-weight: 650; color: {color};")
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        title_row.addWidget(time_label)
        detail_label = QLabel(detail)
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet(f"font-size: 11px; color: {COLORS['muted']};")
        text_box.addLayout(title_row)
        text_box.addWidget(detail_label)

        row.addLayout(marker_box)
        row.addLayout(text_box, 1)
        self.content_layout.addLayout(row)
        if not is_last:
            self.content_layout.addSpacing(4)

    def _make_row(self, label_text: str, value_text: str, value_color: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        label = QLabel(label_text)
        value = QLabel(value_text)
        value.setAlignment(ALIGN_RIGHT)
        label.setStyleSheet(f"font-size: 12px; color: {COLORS['muted']};")
        value.setStyleSheet(f"font-size: 12px; font-weight: 650; color: {value_color};")
        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(value)
        return row

    def _stat_tile(self, label_text: str, value_text: str) -> QFrame:
        tile = QFrame()
        tile.setStyleSheet(
            f"""
            QFrame {{
                background: #FAF9F6;
                border: 0;
                border-radius: 12px;
            }}
            """
        )
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(12, 11, 12, 11)
        layout.setSpacing(3)
        label = QLabel(label_text)
        label.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {COLORS['muted']}; letter-spacing: 1px;")
        value = QLabel(value_text)
        value.setStyleSheet("font-size: 18px; font-weight: 650; color: #3E3C38;")
        layout.addWidget(label)
        layout.addWidget(value)
        return tile
