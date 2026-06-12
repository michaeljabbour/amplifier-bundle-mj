"""Event bus — over-engineered observer system (R13).

The bus is wired up and fires in exactly ONE place (runner.py, on job
completion).  That single call could be replaced with a direct function call
or removed entirely without breaking the test suite.  The full pub/sub
machinery is speculative generality.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


# R14: _format_event duplicates utils.format_result verbatim
# (canonical lives in utils.py; this duplicate is removable)
def _format_event(data: dict) -> str:
    return f"Result({data})"


class EventBus:
    """Minimal publish/subscribe event bus."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, listener: Callable[[Any], None]) -> None:
        self._listeners.setdefault(event_type, []).append(listener)

    def emit(self, event_type: str, data: Any) -> None:
        for listener in self._listeners.get(event_type, []):
            listener(data)


# Module-level singleton — no listeners registered anywhere (R13)
_bus = EventBus()
