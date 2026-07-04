"""Clock abstraction.

T7 (LOAD-BEARING): tests/conftest.py defines ``FakeClock(Clock)``.
Removing the ``Clock`` ABC breaks the conftest.py import, collapsing the
entire test suite.  This is NOT the same as BaseScheduler (R5), which has
no test-level inheritance.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod


class Clock(ABC):
    """Abstract clock interface.

    T7: ``FakeClock`` in tests/conftest.py inherits from this ABC.
    Deleting Clock causes an ``ImportError`` in conftest.py, making every
    test that uses the ``fake_clock`` fixture (and pytest collection itself)
    fail immediately.
    """

    @abstractmethod
    def now(self) -> float:
        """Return current time as a Unix timestamp."""
        ...


class SystemClock(Clock):
    """Production clock backed by ``time.time()``."""

    def now(self) -> float:
        return time.time()
