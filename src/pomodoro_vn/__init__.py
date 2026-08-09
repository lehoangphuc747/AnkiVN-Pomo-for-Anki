"""Anki entrypoint for the PomodoroVN Qt addon."""

try:
    import aqt  # noqa: F401

    from .pomodoro_qt.controller import setup_addon

    setup_addon(__name__)
except ImportError:
    pass
except Exception as exc:
    try:
        from aqt.utils import showWarning

        showWarning(f"PomodoroVN addon failed to load:\n{exc}")
    except Exception:
        raise
