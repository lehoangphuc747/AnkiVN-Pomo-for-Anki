"""Popup dialog showing the changelog for newly installed versions."""

from __future__ import annotations

from aqt.qt import QCheckBox, QDialog, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, Qt

from .changelog import entries_since
from .i18n import current_language, tr
from .style import COLORS, active_colors
from .ui_components import make_button, make_label, set_addon_window_icon


class ChangelogDialog(QDialog):
    """Show "what's new" since the last seen version, with a Don't show again checkbox."""

    def __init__(self, parent: QWidget, last_seen_version: str) -> None:
        super().__init__(parent)
        self._dont_show_again = False
        self.setWindowTitle(tr("changelog.title"))
        set_addon_window_icon(self)
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setMinimumHeight(420)

        c = active_colors()
        lang = current_language()
        if lang not in ("vi", "en"):
            lang = "vi"

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 18)
        root.setSpacing(14)

        title = make_label(tr("changelog.title"))
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {c['red']};")
        subtitle = make_label(tr("changelog.subtitle"), "muted")
        subtitle.setStyleSheet(f"font-size: 12px; color: {c['muted']};")
        root.addWidget(title)
        root.addWidget(subtitle)

        # Scroll area with the entries
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: transparent; border: 0; }}")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 8, 0, 8)
        content_layout.setSpacing(18)

        entries = entries_since(last_seen_version)
        if not entries:
            empty = make_label(tr("changelog.no_changes"), "muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(empty)
        for entry in entries:
            content_layout.addWidget(self._build_entry_block(entry, lang, c))

        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # Footer: checkbox + close button
        footer = QHBoxLayout()
        footer.setSpacing(12)
        self.dont_show_check = QCheckBox(tr("changelog.dont_show_again"))
        self.dont_show_check.setStyleSheet(f"color: {c['text']}; font-size: 12px;")
        footer.addWidget(self.dont_show_check)
        footer.addStretch(1)
        close_button = make_button(tr("common.close"), "primary")
        close_button.clicked.connect(self._on_close)
        footer.addWidget(close_button)
        root.addLayout(footer)

    def _build_entry_block(self, entry: dict, lang: str, c: dict) -> QWidget:
        block = QWidget()
        block.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header_text = f"<span style='color:{c['text']}; font-weight:700;'>v{entry['version']}</span>"
        date = entry.get("date")
        if date:
            header_text += f"  <span style='color:{c['muted']}; font-size:11px;'>· {date}</span>"
        header = QLabel(header_text)
        header.setStyleSheet("font-size: 14px;")
        layout.addWidget(header)

        sections = entry.get(lang) or entry.get("vi") or {}
        for section_name, items in sections.items():
            section_label = make_label(section_name)
            section_label.setStyleSheet(
                f"color: {c['red']}; font-size: 12px; font-weight: 700;"
            )
            layout.addWidget(section_label)
            for item in items:
                bullet = QLabel(f"<span style='color:{c['muted']};'>•</span>  <span style='color:{c['text']};'>{item}</span>")
                bullet.setWordWrap(True)
                bullet.setStyleSheet("font-size: 12px; line-height: 1.5;")
                bullet.setContentsMargins(8, 0, 0, 0)
                layout.addWidget(bullet)
        return block

    def _on_close(self) -> None:
        self._dont_show_again = bool(self.dont_show_check.isChecked())
        self.accept()

    @property
    def dont_show_again(self) -> bool:
        return self._dont_show_again
