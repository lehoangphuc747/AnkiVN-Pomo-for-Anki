"""Small JSON-backed i18n helper for the Pomodoro add-on."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_LANGUAGE = "vi"
FALLBACK_LANGUAGE = "en"
LOCALE_DIR = Path(__file__).resolve().parent / "locales"

_current_language = DEFAULT_LANGUAGE
_cache: dict[str, dict[str, str]] = {}


def set_language(language: str) -> None:
    global _current_language
    normalized = _normalize_language(language)
    if not _load_locale(normalized):
        normalized = DEFAULT_LANGUAGE
    _current_language = normalized


def current_language() -> str:
    return _current_language


def available_languages() -> list[tuple[str, str]]:
    languages = []
    for path in sorted(LOCALE_DIR.glob("*.json")):
        code = path.stem
        data = _load_locale(code)
        label = data.get("language.name", code) if data else code
        languages.append((code, label))
    if not languages:
        return [(DEFAULT_LANGUAGE, DEFAULT_LANGUAGE)]
    return languages


def tr(key: str, **params: Any) -> str:
    text = _lookup(_current_language, key)
    if text is None and _current_language != FALLBACK_LANGUAGE:
        text = _lookup(FALLBACK_LANGUAGE, key)
    if text is None and _current_language != DEFAULT_LANGUAGE:
        text = _lookup(DEFAULT_LANGUAGE, key)
    if text is None:
        text = key
    try:
        return text.format(**params)
    except Exception:
        return text


def _lookup(language: str, key: str) -> str | None:
    data = _load_locale(language)
    value = data.get(key)
    return value if isinstance(value, str) else None


def _load_locale(language: str) -> dict[str, str]:
    language = _normalize_language(language)
    if language in _cache:
        return _cache[language]
    path = LOCALE_DIR / f"{language}.json"
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    _cache[language] = {str(key): str(value) for key, value in data.items()}
    return _cache[language]


def _normalize_language(language: str) -> str:
    value = str(language or DEFAULT_LANGUAGE).strip().replace("_", "-").lower()
    if not value:
        return DEFAULT_LANGUAGE
    return value.split("-", 1)[0]
