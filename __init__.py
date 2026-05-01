"""Anki entrypoint for the PomodoroVN Qt addon."""

try:
    from .pomodoro_qt.controller import setup_addon

    setup_addon(__name__)
except Exception as exc:
    try:
        from aqt.utils import showWarning

        showWarning(f"PomodoroVN addon failed to load:\n{exc}")
    except Exception:
        raise
