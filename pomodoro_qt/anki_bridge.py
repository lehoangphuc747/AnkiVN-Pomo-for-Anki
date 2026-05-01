"""Small adapter around Anki gui_hooks."""

from __future__ import annotations

from typing import Callable


class AnkiBridge:
    def __init__(
        self,
        on_state_changed: Callable[..., None],
        on_reviewer_refreshed: Callable[..., None],
        on_pre_answer: Callable[..., object],
        on_did_answer: Callable[..., object],
        on_reviewer_end: Callable[..., object],
        on_profile_close: Callable[..., None],
    ) -> None:
        self._callbacks = {
            "state_did_change": on_state_changed,
            "reviewer_did_show_question": on_reviewer_refreshed,
            "reviewer_did_show_answer": on_reviewer_refreshed,
            "reviewer_will_answer_card": on_pre_answer,
            "reviewer_did_answer_card": on_did_answer,
            "reviewer_will_end": on_reviewer_end,
            "profile_will_close": on_profile_close,
        }

    def install(self) -> None:
        try:
            from aqt import gui_hooks
        except Exception:
            return
        for name, callback in self._callbacks.items():
            hook = getattr(gui_hooks, name, None)
            if hook is None:
                continue
            try:
                hook.append(callback)
            except Exception:
                pass
