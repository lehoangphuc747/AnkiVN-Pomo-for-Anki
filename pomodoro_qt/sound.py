"""Sound/audio popover for the Pomodoro UI."""

from __future__ import annotations

import html
import re
from typing import Optional

from aqt.qt import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QIcon,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSize,
    QVBoxLayout,
    QWidget,
    Qt,
)

from .i18n import tr
from .popover_shell import PopoverShell
from .style import COLORS, refresh_style
from .ui_components import (
    LOOP_ICON_PATH,
    NEXT_ICON_PATH,
    PAUSE_ICON_PATH,
    PLAY_ICON_PATH,
    PREVIOUS_ICON_PATH,
    SHUFFLE_ICON_PATH,
    SOUNDCLOUD_ICON_PATH,
    make_button,
)


class AudioPopover(PopoverShell):
    def __init__(self) -> None:
        super().__init__(320, spacing=0, shadow_margin=0)
        self._playing = False
        self._loop = False
        self._last_anchor: Optional[QWidget] = None
        self._youtube_web = None

        root = self.content_layout

        root.addLayout(self._make_track_header())
        root.addSpacing(16)
        root.addLayout(self._make_source_controls())
        root.addSpacing(12)
        self._make_youtube_preview()
        root.addWidget(self.youtube_preview)
        root.addSpacing(16)
        root.addLayout(self._make_progress_section())
        root.addSpacing(16)
        root.addLayout(self._make_transport_controls())

        self.preset.currentIndexChanged.connect(self._preset_changed)
        self.load_button.clicked.connect(self._load_youtube)
        self.youtube_input.returnPressed.connect(self._load_youtube)
        self.play_button.clicked.connect(self._toggle_playing)
        self.loop_button.clicked.connect(self._toggle_loop)

    def show_at(self, anchor: QWidget) -> None:
        self._last_anchor = anchor
        super().show_at(anchor, horizontal_alignment="right", vertical_offset=10)

    def toggle_at(self, anchor: QWidget) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show_at(anchor)

    def anchor_is_visible(self) -> bool:
        return self._last_anchor is not None and self._last_anchor.isVisible()

    def state_snapshot(self) -> dict:
        return {
            "preset_index": self.preset.currentIndex(),
            "youtube_url": self.youtube_input.text(),
            "loop": self._loop,
            "playing": self._playing,
        }

    def restore_state(self, state: dict) -> None:
        if not isinstance(state, dict):
            return
        try:
            preset_index = int(state.get("preset_index") or 0)
        except (TypeError, ValueError):
            preset_index = 0
        if 0 <= preset_index < self.preset.count():
            self.preset.setCurrentIndex(preset_index)
        self.youtube_input.setText(str(state.get("youtube_url") or ""))
        if bool(state.get("loop")) != self._loop:
            self._toggle_loop()
        self._set_playing(bool(state.get("playing", False)))

    def _make_track_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        album = QFrame()
        album.setFixedSize(48, 48)
        album.setStyleSheet(
            f"""
            QFrame {{
                background: #F5F4F0;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            """
        )
        album_layout = QVBoxLayout(album)
        album_layout.setContentsMargins(0, 0, 0, 0)
        album_icon = QLabel()
        album_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        album_icon.setPixmap(QIcon(str(SOUNDCLOUD_ICON_PATH)).pixmap(QSize(24, 24)))
        album_icon.setStyleSheet("border: 0;")
        album_layout.addWidget(album_icon)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(2)
        self.title = QLabel(tr("audio.title_lofi"))
        self.title.setStyleSheet("font-size: 14px; font-weight: 650; color: #3E3C38;")
        self.source = QLabel(tr("audio.source_chillhop"))
        self.source.setStyleSheet(f"font-size: 11px; color: {COLORS['muted']};")
        text_box.addStretch(1)
        text_box.addWidget(self.title)
        text_box.addWidget(self.source)
        text_box.addStretch(1)

        header.addWidget(album)
        header.addLayout(text_box, 1)
        return header

    def _make_source_controls(self) -> QVBoxLayout:
        section = QVBoxLayout()
        section.setContentsMargins(0, 0, 0, 0)
        section.setSpacing(10)

        section.addWidget(self._field_label(tr("audio.builtin_label")))
        self.preset = QComboBox()
        self.preset.addItem(tr("audio.title_lofi"), (tr("audio.title_lofi"), tr("audio.source_chillhop")))
        self.preset.addItem(tr("audio.rain"), (tr("audio.rain"), tr("audio.source_builtin")))
        self.preset.addItem(tr("audio.brown_noise"), (tr("audio.brown_noise"), tr("audio.source_builtin")))
        self.preset.addItem(tr("audio.soft_piano"), (tr("audio.soft_piano"), tr("audio.source_builtin")))
        self.preset.setStyleSheet(
            f"""
            QComboBox {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 6px 10px;
                min-height: 26px;
                font-size: 12px;
                font-weight: 600;
                color: {COLORS['text']};
            }}
            QComboBox:focus {{
                border: 1px solid {COLORS['red']};
            }}
            """
        )
        section.addWidget(self.preset)
        section.addSpacing(2)

        section.addWidget(self._field_label(tr("audio.youtube_link")))
        url_row = QHBoxLayout()
        url_row.setContentsMargins(0, 0, 0, 0)
        url_row.setSpacing(8)
        self.youtube_input = QLineEdit()
        self.youtube_input.setPlaceholderText(tr("audio.youtube_placeholder"))
        self.youtube_input.setStyleSheet(
            f"""
            QLineEdit {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 6px 10px;
                min-height: 26px;
                font-size: 12px;
                color: {COLORS['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['red']};
            }}
            """
        )
        self.load_button = make_button(tr("action.load"), "primary", tr("audio.youtube_link"))
        self.load_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLORS['red']};
                color: white;
                border: 0;
                border-radius: 8px;
                padding: 6px 12px;
                min-height: 26px;
                font-size: 12px;
                font-weight: 650;
            }}
            QPushButton:hover {{
                background: {COLORS['red_dark']};
            }}
            """
        )
        url_row.addWidget(self.youtube_input, 1)
        url_row.addWidget(self.load_button)
        section.addLayout(url_row)

        self.status = QLabel(tr("audio.initial_status"))
        self.status.setWordWrap(True)
        self.status.setStyleSheet(f"font-size: 10px; color: {COLORS['muted']}; font-weight: 500;")
        section.addWidget(self.status)
        return section

    def _make_youtube_preview(self) -> None:
        self.youtube_preview = QFrame()
        self.youtube_preview.setFixedHeight(128)
        self.youtube_preview.setStyleSheet(
            f"""
            QFrame {{
                background: {COLORS['bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            """
        )
        layout = QVBoxLayout(self.youtube_preview)
        layout.setContentsMargins(0, 0, 0, 0)
        try:
            from aqt.webview import AnkiWebView

            self._youtube_web = AnkiWebView()
            self._youtube_web.setStyleSheet("background: transparent; border: 0;")
            layout.addWidget(self._youtube_web)
        except Exception:
            placeholder = QLabel(tr("audio.preview"))
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(f"border: 0; color: {COLORS['muted']}; font-size: 11px;")
            layout.addWidget(placeholder)
        self.youtube_preview.hide()

    def _make_progress_section(self) -> QVBoxLayout:
        section = QVBoxLayout()
        section.setContentsMargins(0, 0, 0, 0)
        section.setSpacing(6)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(45)
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
                background: {COLORS['red']};
                border-radius: 3px;
            }}
            """
        )
        time_row = QHBoxLayout()
        time_row.setContentsMargins(0, 0, 0, 0)
        elapsed = QLabel("1:12")
        duration = QLabel("2:45")
        for label in (elapsed, duration):
            label.setStyleSheet(f"font-size: 10px; color: {COLORS['muted']}; font-weight: 600;")
        time_row.addWidget(elapsed)
        time_row.addStretch(1)
        time_row.addWidget(duration)
        section.addWidget(bar)
        section.addLayout(time_row)
        return section

    def _make_transport_controls(self) -> QHBoxLayout:
        controls = QHBoxLayout()
        controls.setContentsMargins(8, 0, 8, 0)
        controls.setSpacing(12)
        self.shuffle_button = self._transport_button(SHUFFLE_ICON_PATH, tr("action.shuffle"), 32, 15)
        self.previous_button = self._transport_button(PREVIOUS_ICON_PATH, tr("action.previous"), 32, 15)
        self.play_button = self._play_button()
        self.next_button = self._transport_button(NEXT_ICON_PATH, tr("action.next"), 32, 15)
        self.loop_button = self._transport_button(LOOP_ICON_PATH, tr("action.loop"), 32, 15)
        controls.addWidget(self.shuffle_button)
        controls.addStretch(1)
        controls.addWidget(self.previous_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.next_button)
        controls.addStretch(1)
        controls.addWidget(self.loop_button)
        return controls

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {COLORS['muted']}; letter-spacing: 1px;")
        return label

    def _transport_button(self, icon_path, tooltip: str, size: int, icon_size: int) -> QPushButton:
        button = QPushButton("")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tooltip)
        button.setFixedSize(size, size)
        button.setIcon(QIcon(str(icon_path)))
        button.setIconSize(QSize(icon_size, icon_size))
        button.setStyleSheet(self._transport_style("transparent"))
        return button

    def _play_button(self) -> QPushButton:
        button = QPushButton("")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tr("tooltip.pause_resume"))
        button.setFixedSize(40, 40)
        button.setIcon(QIcon(str(PLAY_ICON_PATH)))
        button.setIconSize(QSize(17, 17))
        button.setStyleSheet(
            f"""
            QPushButton {{
                background: white;
                border: 1px solid {COLORS['red']};
                border-radius: 20px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: {COLORS['red_light']};
            }}
            """
        )
        return button

    def _transport_style(self, background: str) -> str:
        return f"""
        QPushButton {{
            background: {background};
            border: 0;
            border-radius: 16px;
            padding: 0;
        }}
        QPushButton:hover {{
            background: {COLORS['red_light'] if background != 'transparent' else 'transparent'};
        }}
        """

    def _preset_changed(self) -> None:
        title, source = self.preset.currentData()
        self.title.setText(title)
        self.source.setText(source)
        self.youtube_preview.hide()
        self._clear_youtube_preview()
        self._set_status(tr("audio.using_builtin"), False)

    def _load_youtube(self) -> None:
        video_id = _youtube_video_id(self.youtube_input.text())
        if not video_id:
            self._set_status(tr("audio.invalid_youtube"), True)
            return
        self.title.setText(tr("audio.youtube_title"))
        self.source.setText(tr("audio.youtube_source"))
        self.youtube_preview.show()
        self._load_youtube_preview(video_id)
        self._set_status(tr("audio.loaded_youtube"), False)
        self._set_playing(True)
        if self.isVisible() and self._last_anchor is not None:
            self.show_at(self._last_anchor)
        else:
            self.adjustSize()

    def _load_youtube_preview(self, video_id: str) -> None:
        if self._youtube_web is None:
            return
        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"
        iframe_title = html.escape(tr("audio.youtube_title"), quote=True)
        html_doc = (
            "<body style='margin:0;background:#F8F7F3;overflow:hidden;'>"
            f"<iframe src='{embed_url}' title='{iframe_title}' "
            "allow='autoplay; encrypted-media; picture-in-picture' allowfullscreen "
            "style='border:0;width:100%;height:100%;'></iframe>"
            "</body>"
        )
        try:
            self._youtube_web.stdHtml(html_doc)
        except Exception:
            try:
                self._youtube_web.setHtml(html_doc)
            except Exception:
                pass

    def _clear_youtube_preview(self) -> None:
        if self._youtube_web is None:
            return
        try:
            self._youtube_web.stdHtml("<body style='margin:0;background:#F8F7F3;'></body>")
        except Exception:
            try:
                self._youtube_web.setHtml("<body style='margin:0;background:#F8F7F3;'></body>")
            except Exception:
                pass

    def _set_status(self, text: str, is_error: bool) -> None:
        self.status.setText(text)
        color = COLORS["red"] if is_error else COLORS["muted"]
        self.status.setStyleSheet(f"font-size: 10px; color: {color}; font-weight: 500;")

    def _toggle_playing(self) -> None:
        self._set_playing(not self._playing)

    def _set_playing(self, playing: bool) -> None:
        self._playing = playing
        icon_path = PAUSE_ICON_PATH if playing else PLAY_ICON_PATH
        self.play_button.setIcon(QIcon(str(icon_path)))
        self.play_button.setIconSize(QSize(15 if playing else 17, 15 if playing else 17))
        self.play_button.setGraphicsEffect(None)
        refresh_style(self.play_button)

    def _toggle_loop(self) -> None:
        self._loop = not self._loop
        background = COLORS["red_light"] if self._loop else "transparent"
        self.loop_button.setStyleSheet(self._transport_style(background))
        self.loop_button.setProperty("active", self._loop)
        refresh_style(self.loop_button)


def _youtube_video_id(raw_url: str) -> Optional[str]:
    value = raw_url.strip()
    if not value:
        return None
    match = re.search(r"(?:v=|youtu\.be/|embed/|shorts/|live/)([A-Za-z0-9_-]{11})", value)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    return None


__all__ = ["AudioPopover"]
