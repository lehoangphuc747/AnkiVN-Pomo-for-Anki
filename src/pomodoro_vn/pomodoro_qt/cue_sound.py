"""One-shot cue sounds for Pomodoro / break transitions.

Plays short notification sounds when a Pomodoro or break starts/ends. The
underlying ``QMediaPlayer`` instances are cached so the player object isn't
garbage-collected mid-playback.

Failures are silent: we never want a missing codec or audio device to crash
the add-on, since these cues are purely a nice-to-have.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


try:
    from aqt.qt import QUrl
except Exception:  # pragma: no cover - depends on Anki's Qt binding
    QUrl = None

try:  # pragma: no cover - exercised inside Anki
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

    QMediaContent = None
    _MULTIMEDIA_API = "qt6"
except Exception:  # pragma: no cover - depends on Anki's Qt binding
    try:
        from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

        QAudioOutput = None
        _MULTIMEDIA_API = "qt5"
    except Exception:
        QAudioOutput = None
        QMediaContent = None
        QMediaPlayer = None
        _MULTIMEDIA_API = ""


SOUND_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"
START_CUE_PATH = SOUND_DIR / "cue_start.mp3"
END_CUE_PATH = SOUND_DIR / "cue_end.mp3"
LOG_PATH = Path(__file__).resolve().parent.parent / "pomodoro_qt.log"

DEFAULT_VOLUME = 0.7


_players: Dict[str, "object"] = {}
_audio_outputs: Dict[str, "object"] = {}


def _log(message: str) -> None:
    try:
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} cue_sound: {message}\n")
    except Exception:
        pass


def _play(path: Path, key: str) -> None:
    if QUrl is None or QMediaPlayer is None:
        return
    if not path.is_file():
        _log(f"missing cue file: {path}")
        return

    player = _players.get(key)
    audio_output = _audio_outputs.get(key)
    try:
        if player is None:
            player = QMediaPlayer()
            if _MULTIMEDIA_API == "qt6" and QAudioOutput is not None:
                audio_output = QAudioOutput()
                audio_output.setVolume(DEFAULT_VOLUME)
                player.setAudioOutput(audio_output)
            elif hasattr(player, "setVolume"):
                try:
                    player.setVolume(int(DEFAULT_VOLUME * 100))
                except Exception:
                    pass
            _players[key] = player
            if audio_output is not None:
                _audio_outputs[key] = audio_output

        url = QUrl.fromLocalFile(str(path))
        if _MULTIMEDIA_API == "qt6":
            player.setSource(url)
        else:
            if QMediaContent is None:
                return
            player.setMedia(QMediaContent(url))
        # Always restart from the beginning for one-shot cues.
        try:
            player.setPosition(0)
        except Exception:
            pass
        player.play()
    except Exception as exc:
        _log(f"error playing {path.name}: {exc}")


def play_start_cue() -> None:
    """Play a short cue when a Pomodoro or break starts."""
    _play(START_CUE_PATH, "start")


def play_end_cue() -> None:
    """Play a short cue when a Pomodoro or break ends."""
    _play(END_CUE_PATH, "end")
