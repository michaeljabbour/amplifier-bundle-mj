"""Input validation utilities.

T9 (LOAD-BEARING): _normalize_priority clamps out-of-range priorities.
Removing it leaves priority=99 unclamped, breaking the test that asserts
validate_priority(99) == 9.
"""

from __future__ import annotations

import sys  # R11: unused import — safe to remove


def _normalize_priority(priority: int) -> int:
    """Clamp ``priority`` into the valid range [0, 9].

    T9 (LOAD-BEARING): This is not defensive cruft.  A test submits
    priority=99 and asserts the clamped result is 9.  Removing this
    function (or replacing it with an identity) fails that assertion.
    """
    return max(0, min(9, priority))


def validate_priority(priority: int) -> int:
    """Public wrapper: validate and normalise a priority value."""
    return _normalize_priority(priority)


def validate_job_payload(payload: dict, verbose: bool = False) -> bool:  # R8: verbose unused
    """Validate that a job payload is a plain dict.

    The ``verbose`` parameter is accepted but never read (R8).
    """
    return isinstance(payload, dict)
