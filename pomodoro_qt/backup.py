"""JSON backup helpers for Pomodoro settings and persistent state."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import PomodoroSettings
from .storage import STATE_VERSION, default_state


BACKUP_KIND = "pomodoro_qt_backup"
BACKUP_VERSION = 1


class BackupError(ValueError):
    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def build_backup(settings: PomodoroSettings, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": BACKUP_KIND,
        "version": BACKUP_VERSION,
        "exported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "settings": settings.to_config(),
        "state": _normalized_state(state),
    }


def write_backup(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)


def read_backup(path: str | Path) -> tuple[PomodoroSettings, dict[str, Any]]:
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        raise BackupError("backup.error.invalid_json") from exc
    return parse_backup(payload)


def parse_backup(payload: object) -> tuple[PomodoroSettings, dict[str, Any]]:
    if not isinstance(payload, dict):
        raise BackupError("backup.error.invalid_format")
    if payload.get("kind") != BACKUP_KIND:
        raise BackupError("backup.error.invalid_format")
    if payload.get("version") != BACKUP_VERSION:
        raise BackupError("backup.error.unsupported_version")

    raw_settings = payload.get("settings")
    raw_state = payload.get("state")
    if not isinstance(raw_settings, dict) or not isinstance(raw_state, dict):
        raise BackupError("backup.error.missing_sections")

    return PomodoroSettings.from_config(raw_settings), _normalized_state(raw_state)


def _normalized_state(state: object) -> dict[str, Any]:
    payload = default_state()
    if isinstance(state, dict):
        payload.update(state)
    payload.pop("_loaded_version", None)
    payload["version"] = STATE_VERSION
    return payload
