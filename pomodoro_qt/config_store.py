"""Configuration loading and saving through Anki's addon manager."""

from __future__ import annotations

from typing import Any

from .models import PomodoroSettings


DEFAULT_CONFIG = PomodoroSettings().to_config()


class ConfigStore:
    def __init__(self, mw: Any, addon_package: str) -> None:
        self._mw = mw
        self._addon_package = addon_package

    def load(self) -> PomodoroSettings:
        config = DEFAULT_CONFIG.copy()
        try:
            stored = self._mw.addonManager.getConfig(self._addon_package) or {}
            if isinstance(stored, dict):
                config.update(stored)
        except Exception:
            pass
        return PomodoroSettings.from_config(config)

    def save(self, settings: PomodoroSettings) -> None:
        try:
            self._mw.addonManager.writeConfig(self._addon_package, settings.to_config())
        except Exception:
            pass
