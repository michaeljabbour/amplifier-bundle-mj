"""Utility helpers — canonical location (R14).

``format_result`` here is the canonical version.  It is duplicated verbatim
in runner._format_result and events._format_event (R14).  Those duplicates
are safe to remove; consolidate to this module.
"""

from __future__ import annotations

import re  # R11: unused import — also duplicated from repository.py; safe to remove


def format_result(result: dict) -> str:
    """Format a result dict as a human-readable string.

    R14 (canonical): duplicated in runner._format_result and
    events._format_event.  Those copies are removable; this is the one to keep.
    """
    return f"Result({result})"


def chunked(iterable: list, size: int) -> list[list]:
    """Split ``iterable`` into chunks of at most ``size`` items."""
    return [iterable[i : i + size] for i in range(0, len(iterable), size)]
