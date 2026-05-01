"""Profile-local persistence for Pomodoro runtime data."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


STATE_VERSION = 2
STATE_FILENAME = "pomodoro_qt_state.json"


def default_state() -> dict:
    return {
        "version": STATE_VERSION,
        "active_session": None,
        "timer_state": None,
        "history": [],
        "daily_stats": {},
        "total_xp": 0,
        "session_index": 1,
        "current_streak_days": 0,
        "longest_streak_days": 0,
        "audio_state": {},
    }


class PomodoroDataStore:
    """Read/write small Pomodoro state next to the active Anki profile."""

    def __init__(self, mw: Any, addon_package: str) -> None:
        self._mw = mw
        self._addon_package = addon_package
        self.path = self._resolve_path()
        self.last_error: Exception | None = None

    def load(self) -> dict:
        state = default_state()
        try:
            if not self.path.exists():
                return state
            with self.path.open("r", encoding="utf-8") as handle:
                stored = json.load(handle)
            if isinstance(stored, dict):
                state["_loaded_version"] = stored.get("version", 0)
                state.update(stored)
        except Exception as exc:
            self.last_error = exc
            self._log_error("load", exc)
            return state
        state["version"] = STATE_VERSION
        return state

    def save(self, state: dict) -> bool:
        payload = default_state()
        if isinstance(state, dict):
            payload.update(state)
        payload["version"] = STATE_VERSION
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.path.with_suffix(".tmp")
            with tmp_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            tmp_path.replace(self.path)
        except Exception as exc:
            self.last_error = exc
            self._log_error("save", exc)
            return False
        self.last_error = None
        return True

    def _log_error(self, action: str, exc: Exception) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            log_path = self.path.with_name("pomodoro_qt.log")
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"{timestamp} storage.{action}: {type(exc).__name__}: {exc}\n")
        except Exception:
            pass

    def _resolve_path(self) -> Path:
        profile_folder = None
        try:
            pm = getattr(self._mw, "pm", None)
            profile_folder_fn = getattr(pm, "profileFolder", None)
            if callable(profile_folder_fn):
                profile_folder = profile_folder_fn()
        except Exception:
            profile_folder = None

        if profile_folder:
            return Path(profile_folder) / STATE_FILENAME

        try:
            addon_folder = self._mw.addonManager.addonsFolder(self._addon_package)
            return Path(addon_folder) / STATE_FILENAME
        except Exception:
            return Path(__file__).resolve().parent.parent / STATE_FILENAME
