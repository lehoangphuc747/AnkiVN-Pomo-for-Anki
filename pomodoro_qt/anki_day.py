"""Shared Anki-day helpers for revlog-backed metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional


def anki_rollover_seconds(col: Any) -> int:
    conf = getattr(col, "conf", None)
    if isinstance(conf, dict):
        try:
            rollover_hour = int(conf.get("rollover"))
            return max(0, min(23, rollover_hour)) * 3600
        except (TypeError, ValueError):
            pass
    cutoff = _anki_day_cutoff(col)
    if cutoff is None:
        return 4 * 3600
    try:
        rollover = datetime.fromtimestamp(int(cutoff))
    except (OSError, OverflowError, TypeError, ValueError):
        return 4 * 3600
    return max(0, min(23 * 3600 + 59 * 60, rollover.hour * 3600 + rollover.minute * 60))


def anki_today_start(db: Any, rollover_seconds: int) -> int:
    if int(rollover_seconds) % 3600 == 0:
        modifier = f"-{int(rollover_seconds) // 3600} hours"
    else:
        modifier = f"-{max(0, int(rollover_seconds))} seconds"
    try:
        value = db.scalar(
            "SELECT CAST(STRFTIME('%s', 'now', ?, 'localtime', 'start of day') AS int)",
            modifier,
        )
        return int(value)
    except Exception:
        return int(datetime.now().timestamp())


def day_key(day_start: int) -> str:
    return datetime.fromtimestamp(day_start).date().isoformat()


def seconds_until_cutoff(today_start: int, rollover_seconds: int) -> int:
    next_cutoff = int(today_start) + 86400 + max(0, int(rollover_seconds))
    now = int(datetime.now().timestamp())
    while next_cutoff <= now:
        next_cutoff += 86400
    return max(0, next_cutoff - now)


def _anki_day_cutoff(col: Any) -> Optional[int]:
    sched = getattr(col, "sched", None)
    for name in ("day_cutoff", "dayCutoff"):
        value = getattr(sched, name, None)
        if callable(value):
            try:
                value = value()
            except Exception:
                continue
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


__all__ = ["anki_rollover_seconds", "anki_today_start", "day_key", "seconds_until_cutoff"]
