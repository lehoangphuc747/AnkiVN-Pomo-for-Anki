"""Sound/audio popover for the Pomodoro UI."""

from __future__ import annotations

import html
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from aqt.qt import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QIcon,
    QLabel,
    QLineEdit,
    QPushButton,
    QSize,
    QSizePolicy,
    QSlider,
    QTimer,
    QVBoxLayout,
    QWidget,
    Qt,
)

try:
    from aqt.qt import QUrl
except Exception:  # pragma: no cover - depends on Anki's Qt binding
    QUrl = None

try:  # pragma: no cover - exercised inside Anki
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

    try:
        from PyQt6.QtMultimedia import QSoundEffect
    except Exception:
        QSoundEffect = None

    QMediaContent = None
    QT_MULTIMEDIA_API = "qt6"
except Exception:  # pragma: no cover - depends on Anki's Qt binding
    try:
        from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

        try:
            from PyQt5.QtMultimedia import QSoundEffect
        except Exception:
            QSoundEffect = None

        QAudioOutput = None
        QT_MULTIMEDIA_API = "qt5"
    except Exception:
        QAudioOutput = None
        QMediaContent = None
        QMediaPlayer = None
        QSoundEffect = None
        QT_MULTIMEDIA_API = ""

from .i18n import tr
from .audio_volume import (
    DEFAULT_LOCAL_VOLUME_PERCENT,
    LOCAL_VOLUME_STATE_KEY,
    clamp_local_volume_percent,
    local_volume_fraction,
    local_volume_label,
)
from .popover_shell import PopoverShell
from .style import COLORS, refresh_style
from .ui_components import (
    NEXT_ICON_PATH,
    PAUSE_ICON_PATH,
    PLAY_ICON_PATH,
    PREVIOUS_ICON_PATH,
    SHUFFLE_ICON_PATH,
    SOUNDCLOUD_ICON_PATH,
    make_button,
)


SOUND_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"
LOG_PATH = Path(__file__).resolve().parent.parent / "pomodoro_qt.log"
DEFAULT_YOUTUBE_URL = "https://youtu.be/l3zE0R2M7XE?si=fAHY-EjhOXFwznYM"

BUILTIN_SOUNDS = (
    {
        "title_key": "audio.short_rain",
        "source_key": "audio.source_dmk67",
        "filename": "392980__dmk67__short-rain-loop.wav",
    },
    {
        "title_key": "audio.slow_rain",
        "source_key": "audio.source_unfa",
        "filename": "177479__unfa__slowly-raining-loop.wav",
    },
    {
        "title_key": "audio.skylight_rain",
        "source_key": "audio.source_deadrobotmusic",
        "filename": "663947__deadrobotmusic__looping-rain-on-skylight-foley-texture.wav",
    },
)


class AudioPopover(PopoverShell):
    def __init__(self) -> None:
        super().__init__(320, spacing=0, shadow_margin=0)
        self._playing = False
        self._loop = True
        self._last_anchor: Optional[QWidget] = None
        self._youtube_web = None
        self._player = None
        self._audio_output = None
        self._sound_effect = None
        self._sound_effect_path: Optional[Path] = None
        self._active_audio_path: Optional[Path] = None
        self._loaded_audio_path: Optional[Path] = None
        self._local_volume_percent = DEFAULT_LOCAL_VOLUME_PERCENT
        self._init_audio_player()

        root = self.content_layout

        root.addLayout(self._make_track_header())
        root.addSpacing(16)
        root.addLayout(self._make_source_controls())
        root.addSpacing(12)
        self._make_youtube_preview()
        root.addWidget(self.youtube_preview)
        root.addSpacing(16)
        root.addLayout(self._make_transport_controls())

        self.preset.currentIndexChanged.connect(self._preset_changed)
        self.load_button.clicked.connect(self._load_youtube)
        self.youtube_input.returnPressed.connect(self._load_youtube)
        self.play_button.clicked.connect(self._toggle_playing)
        self.previous_button.clicked.connect(self._select_previous_builtin)
        self.next_button.clicked.connect(self._select_next_builtin)
        self.shuffle_button.clicked.connect(self._shuffle_builtin)
        self.volume_slider.valueChanged.connect(self._local_volume_changed)
        self._preset_changed()

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
            LOCAL_VOLUME_STATE_KEY: self._local_volume_percent,
        }

    def restore_state(self, state: dict) -> None:
        if not isinstance(state, dict):
            return
        self._set_local_volume_percent(state.get(LOCAL_VOLUME_STATE_KEY), sync_slider=True)
        try:
            preset_index = int(state.get("preset_index") or 0)
        except (TypeError, ValueError):
            preset_index = 0
        if 0 <= preset_index < self.preset.count():
            self.preset.setCurrentIndex(preset_index)
        self.youtube_input.setText(str(state.get("youtube_url") or DEFAULT_YOUTUBE_URL))
        self._set_playing(False)
        self._update_volume_ui_state()

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
        self.title = QLabel(tr("audio.short_rain"))
        self.title.setStyleSheet("font-size: 14px; font-weight: 650; color: #3E3C38;")
        self.source = QLabel(tr("audio.source_dmk67"))
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
        for sound in BUILTIN_SOUNDS:
            title = tr(sound["title_key"])
            source = tr(sound["source_key"])
            self.preset.addItem(title, {**sound, "title": title, "source": source})
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

        section.addWidget(self._field_label(tr("audio.local_volume")))
        volume_row = QHBoxLayout()
        volume_row.setContentsMargins(0, 0, 0, 0)
        volume_row.setSpacing(8)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setSingleStep(1)
        self.volume_slider.setPageStep(5)
        self.volume_slider.setValue(self._local_volume_percent)
        self.volume_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.volume_slider.setStyleSheet(self._volume_slider_style())
        self.volume_value = QLabel(local_volume_label(self._local_volume_percent))
        self.volume_value.setFixedWidth(42)
        self.volume_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.volume_value.setStyleSheet(f"font-size: 11px; font-weight: 650; color: {COLORS['muted']};")
        volume_row.addWidget(self.volume_slider, 1)
        volume_row.addWidget(self.volume_value, 0)
        section.addLayout(volume_row)
        section.addSpacing(2)

        section.addWidget(self._field_label(tr("audio.youtube_link")))
        url_row = QHBoxLayout()
        url_row.setContentsMargins(0, 0, 0, 0)
        url_row.setSpacing(8)
        self.youtube_input = QLineEdit()
        self.youtube_input.setPlaceholderText(tr("audio.youtube_placeholder"))
        self.youtube_input.setText(DEFAULT_YOUTUBE_URL)
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
        self.youtube_preview.setFixedHeight(210)
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
        layout.setContentsMargins(1, 1, 1, 1)
        try:
            from aqt.webview import AnkiWebView

            self._youtube_web = AnkiWebView()
            self._youtube_web.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._youtube_web.setStyleSheet("background: transparent; border: 0;")
            layout.addWidget(self._youtube_web)
        except Exception:
            placeholder = QLabel(tr("audio.preview"))
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(f"border: 0; color: {COLORS['muted']}; font-size: 11px;")
            layout.addWidget(placeholder)
        self.youtube_preview.hide()

    def _make_transport_controls(self) -> QHBoxLayout:
        controls = QHBoxLayout()
        controls.setContentsMargins(8, 0, 8, 0)
        controls.setSpacing(12)
        self.shuffle_button = self._transport_button(SHUFFLE_ICON_PATH, tr("action.shuffle"), 32, 15)
        self.previous_button = self._transport_button(PREVIOUS_ICON_PATH, tr("action.previous"), 32, 15)
        self.play_button = self._play_button()
        self.next_button = self._transport_button(NEXT_ICON_PATH, tr("action.next"), 32, 15)
        controls.addWidget(self.shuffle_button)
        controls.addStretch(1)
        controls.addWidget(self.previous_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.next_button)
        controls.addStretch(1)
        controls.addSpacing(32)
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
        sound = self.preset.currentData()
        if not isinstance(sound, dict):
            return
        title = str(sound.get("title") or "")
        source = str(sound.get("source") or "")
        self.title.setText(title)
        self.source.setText(source)
        self.youtube_preview.hide()
        self._clear_youtube_preview()
        self._active_audio_path = SOUND_DIR / str(sound.get("filename") or "")
        self._loaded_audio_path = None
        self._apply_local_volume()
        self._update_volume_ui_state()
        if self._playing:
            self._playing = self._play_active_builtin()
            self._refresh_play_button(self._playing)
        else:
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
        self._stop_builtin()
        self._set_playing(True)
        self._update_volume_ui_state()
        if self.isVisible() and self._last_anchor is not None:
            self.show_at(self._last_anchor)
        else:
            self.adjustSize()

    def _load_youtube_preview(self, video_id: str) -> None:
        if self._youtube_web is None:
            return
        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0&playsinline=1"
        iframe_title = html.escape(tr("audio.youtube_title"), quote=True)
        html_doc = (
            "<!doctype html>"
            "<html>"
            "<head>"
            "<meta charset='utf-8'>"
            "<style>"
            "html,body{width:100%;height:100%;margin:0;padding:0;overflow:hidden;background:#000;}"
            ".player{position:fixed;inset:0;}"
            "iframe{display:block;width:100%;height:100%;border:0;}"
            "</style>"
            "</head>"
            "<body>"
            "<div class='player'>"
            f"<iframe src='{embed_url}' title='{iframe_title}' "
            "allow='autoplay; encrypted-media; picture-in-picture' allowfullscreen></iframe>"
            "</div>"
            "</body>"
            "</html>"
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
        actual_playing = playing
        if self.youtube_preview.isVisible():
            if not playing:
                self._clear_youtube_preview()
        elif playing:
            actual_playing = self._play_active_builtin()
        else:
            self._pause_builtin()

        self._playing = actual_playing
        self._refresh_play_button(actual_playing)

    def _refresh_play_button(self, playing: bool) -> None:
        icon_path = PAUSE_ICON_PATH if playing else PLAY_ICON_PATH
        self.play_button.setIcon(QIcon(str(icon_path)))
        size = 15 if playing else 17
        self.play_button.setIconSize(QSize(size, size))
        self.play_button.setGraphicsEffect(None)
        refresh_style(self.play_button)

    def _local_audio_available(self) -> bool:
        return self._player is not None or self._sound_effect is not None

    def _volume_slider_style(self) -> str:
        return f"""
        QSlider::groove:horizontal {{
            height: 6px;
            background: {COLORS['border']};
            border-radius: 3px;
        }}
        QSlider::sub-page:horizontal {{
            background: {COLORS['red']};
            border-radius: 3px;
        }}
        QSlider::add-page:horizontal {{
            background: {COLORS['soft']};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: white;
            border: 1px solid {COLORS['red']};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QSlider::groove:horizontal:disabled {{
            background: {COLORS['border']};
        }}
        QSlider::handle:horizontal:disabled {{
            border-color: {COLORS['muted_light']};
        }}
        """

    def _update_volume_ui_state(self) -> None:
        enabled = self._local_audio_available() and not self.youtube_preview.isVisible()
        self.volume_slider.setEnabled(enabled)
        self.volume_value.setEnabled(enabled)

    def _local_volume_changed(self, value: int) -> None:
        self._set_local_volume_percent(value)

    def _set_local_volume_percent(self, value: object, *, sync_slider: bool = False) -> None:
        percent = clamp_local_volume_percent(value, DEFAULT_LOCAL_VOLUME_PERCENT)
        self._local_volume_percent = percent
        if hasattr(self, "volume_value"):
            self.volume_value.setText(local_volume_label(percent))
        if sync_slider and hasattr(self, "volume_slider"):
            previous = self.volume_slider.blockSignals(True)
            try:
                self.volume_slider.setValue(percent)
            finally:
                self.volume_slider.blockSignals(previous)
        self._apply_local_volume()

    def _apply_local_volume(self) -> None:
        percent = self._local_volume_percent
        fraction = local_volume_fraction(percent)
        if self._audio_output is not None:
            try:
                self._audio_output.setVolume(fraction)
            except Exception:
                pass
        if self._player is not None and hasattr(self._player, "setVolume"):
            try:
                self._player.setVolume(percent)
            except Exception:
                pass
        if self._sound_effect is not None:
            try:
                self._sound_effect.setVolume(fraction)
            except Exception:
                pass

    def _init_audio_player(self) -> None:
        if QUrl is None:
            return
        self._init_sound_effect()
        if QMediaPlayer is None:
            return
        try:
            self._player = QMediaPlayer(self)
            if QT_MULTIMEDIA_API == "qt6" and QAudioOutput is not None:
                self._audio_output = QAudioOutput(self)
                self._player.setAudioOutput(self._audio_output)
            if hasattr(self._player, "mediaStatusChanged"):
                self._player.mediaStatusChanged.connect(self._media_status_changed)
            if hasattr(self._player, "errorOccurred"):
                self._player.errorOccurred.connect(self._player_error)
            elif hasattr(self._player, "error"):
                self._player.error.connect(self._player_error)
            self._apply_local_volume()
        except Exception as exc:
            self._log_audio_error(f"Could not initialize QMediaPlayer: {exc}")
            self._player = None
            self._audio_output = None

    def _init_sound_effect(self) -> None:
        if QSoundEffect is None:
            return
        try:
            self._sound_effect = QSoundEffect(self)
            self._apply_local_volume()
        except Exception as exc:
            self._log_audio_error(f"Could not initialize QSoundEffect: {exc}")
            self._sound_effect = None

    def _play_active_builtin(self) -> bool:
        path = self._active_audio_path
        if path is None or not path.is_file():
            self._set_status(tr("audio.local_missing"), True)
            self._log_audio_error(f"Missing built-in sound: {path}")
            return False
        if self._should_use_sound_effect(path):
            return self._play_sound_effect(path)
        if self._player is None:
            self._set_status(tr("audio.local_unavailable"), True)
            self._log_audio_error("QMediaPlayer is unavailable.")
            return False
        try:
            self._stop_sound_effect()
            if self._loaded_audio_path != path:
                url = QUrl.fromLocalFile(str(path))
                if QT_MULTIMEDIA_API == "qt6":
                    self._player.setSource(url)
                else:
                    self._player.setMedia(QMediaContent(url))
                self._loaded_audio_path = path
            self._apply_media_player_loop_setting()
            self._apply_local_volume()
            self._player.play()
            self._set_status(tr("audio.using_builtin"), False)
            QTimer.singleShot(300, self._verify_playback_started)
            return True
        except Exception as exc:
            self._show_audio_error(str(exc))
            return False

    def _should_use_sound_effect(self, path: Path) -> bool:
        return self._loop and self._sound_effect is not None and path.suffix.lower() == ".wav"

    def _play_sound_effect(self, path: Path) -> bool:
        if self._sound_effect is None or QUrl is None:
            return False
        try:
            if self._player is not None:
                self._player.stop()
            if self._sound_effect_path != path:
                self._sound_effect.stop()
                self._sound_effect.setSource(QUrl.fromLocalFile(str(path)))
                self._sound_effect_path = path
            self._apply_sound_effect_loop_setting()
            self._apply_local_volume()
            self._sound_effect.play()
            self._set_status(tr("audio.using_builtin"), False)
            return True
        except Exception as exc:
            self._show_audio_error(str(exc))
            return False

    def _pause_builtin(self) -> None:
        self._stop_sound_effect()
        if self._player is not None:
            try:
                self._player.pause()
            except Exception:
                pass

    def _stop_builtin(self) -> None:
        self._stop_sound_effect()
        if self._player is not None:
            try:
                self._player.stop()
            except Exception:
                pass

    def _stop_sound_effect(self) -> None:
        if self._sound_effect is not None:
            try:
                self._sound_effect.stop()
            except Exception:
                pass

    def _media_status_changed(self, status) -> None:
        if not self._is_end_of_media(status):
            return
        if self._loop and self._playing:
            if self._media_player_has_native_looping():
                return
            self._playing = self._play_active_builtin()
            self._refresh_play_button(self._playing)
        else:
            self._set_playing(False)

    def _apply_active_loop_setting(self) -> None:
        path = self._active_audio_path
        if path is None or self.youtube_preview.isVisible():
            return
        if self._sound_effect is not None and self._sound_effect_path == path:
            self._apply_sound_effect_loop_setting()
        self._apply_media_player_loop_setting()
        if self._playing and path.suffix.lower() == ".wav":
            self._playing = self._play_active_builtin()
            self._refresh_play_button(self._playing)

    def _apply_sound_effect_loop_setting(self) -> None:
        if self._sound_effect is None:
            return
        try:
            self._sound_effect.setLoopCount(self._sound_effect_loop_count())
        except Exception:
            pass

    def _sound_effect_loop_count(self) -> int:
        if not self._loop or QSoundEffect is None:
            return 1
        loop_enum = getattr(QSoundEffect, "Loop", None)
        infinite = getattr(loop_enum, "Infinite", None) if loop_enum is not None else None
        if infinite is None:
            infinite = getattr(QSoundEffect, "Infinite", -2)
        return int(getattr(infinite, "value", infinite))

    def _apply_media_player_loop_setting(self) -> None:
        if self._player is None or not hasattr(self._player, "setLoops"):
            return
        try:
            self._player.setLoops(self._media_player_loop_count())
        except Exception:
            pass

    def _media_player_loop_count(self) -> int:
        if not self._loop or QMediaPlayer is None:
            return 1
        infinite = getattr(QMediaPlayer, "Infinite", -1)
        return int(getattr(infinite, "value", infinite))

    def _media_player_has_native_looping(self) -> bool:
        return self._player is not None and hasattr(self._player, "setLoops")

    def _is_end_of_media(self, status) -> bool:
        if QMediaPlayer is None:
            return False
        media_status = getattr(QMediaPlayer, "MediaStatus", None)
        end_status = getattr(media_status, "EndOfMedia", None) if media_status is not None else None
        if end_status is None:
            end_status = getattr(QMediaPlayer, "EndOfMedia", None)
        return end_status is not None and status == end_status

    def _select_previous_builtin(self) -> None:
        count = self.preset.count()
        if count:
            self.preset.setCurrentIndex((self.preset.currentIndex() - 1) % count)

    def _select_next_builtin(self) -> None:
        count = self.preset.count()
        if count:
            self.preset.setCurrentIndex((self.preset.currentIndex() + 1) % count)

    def _shuffle_builtin(self) -> None:
        count = self.preset.count()
        if count < 2:
            return
        current = self.preset.currentIndex()
        choices = [index for index in range(count) if index != current]
        self.preset.setCurrentIndex(random.choice(choices))

    def _player_error(self, *_args) -> None:
        message = ""
        if len(_args) >= 2 and _args[1]:
            message = str(_args[1])
        if not message and self._player is not None:
            try:
                message = str(self._player.errorString())
            except Exception:
                message = ""
        self._playing = False
        self._refresh_play_button(False)
        self._show_audio_error(message)

    def _verify_playback_started(self) -> None:
        if (self._player is None and self._sound_effect is None) or not self._playing or self.youtube_preview.isVisible():
            return
        if self._sound_effect is not None:
            try:
                if self._sound_effect.isPlaying():
                    return
            except Exception:
                pass
        try:
            if self._player_is_playing():
                return
        except Exception as exc:
            self._log_audio_error(f"Could not verify playback state: {exc}")
            return
        self._playing = False
        self._refresh_play_button(False)
        self._show_audio_error(self._player_error_string())

    def _player_is_playing(self) -> bool:
        if self._player is None or QMediaPlayer is None:
            return False
        if hasattr(self._player, "playbackState"):
            state = self._player.playbackState()
            playback_state = getattr(QMediaPlayer, "PlaybackState", None)
            playing_state = getattr(playback_state, "PlayingState", None) if playback_state is not None else None
            return playing_state is not None and state == playing_state
        if hasattr(self._player, "state"):
            state = self._player.state()
            playing_state = getattr(QMediaPlayer, "PlayingState", None)
            return playing_state is not None and state == playing_state
        return False

    def _player_error_string(self) -> str:
        if self._player is None:
            return ""
        try:
            return str(self._player.errorString())
        except Exception:
            return ""

    def _show_audio_error(self, message: str = "") -> None:
        message = str(message or "").strip()
        status = tr("audio.local_unavailable")
        if message:
            status = f"{status} {message}"
        self._set_status(status, True)
        self._log_audio_error(status)

    def _log_audio_error(self, message: str) -> None:
        try:
            timestamp = datetime.now().isoformat(timespec="seconds")
            with LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(f"{timestamp} audio: {message}\n")
        except Exception:
            pass

    def cleanup(self) -> None:
        """Detach the embedded YouTube AnkiWebView before the popover is deleted."""
        web = getattr(self, "_youtube_web", None)
        if web is None:
            return
        try:
            if hasattr(web, "cleanup") and callable(web.cleanup):
                web.cleanup()
        except Exception:
            pass
        self._youtube_web = None


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
