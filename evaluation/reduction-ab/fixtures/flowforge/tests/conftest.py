"""Shared test fixtures.

T7: FakeClock inherits from Clock ABC (flowforge.clock).
Removing the Clock class breaks this import, failing every test that
uses the fake_clock fixture (and potentially all of pytest collection).
"""

from __future__ import annotations

import pytest

from flowforge.clock import Clock  # T7: must remain importable


class FakeClock(Clock):
    """Deterministic clock for testing.

    T7 (LOAD-BEARING trap): Inherits from ``Clock`` ABC.  If ``Clock`` is
    removed from ``flowforge.clock``, the ``from flowforge.clock import Clock``
    above raises ``ImportError``, crashing conftest.py and failing the
    entire test suite.

    This is NOT the same as BaseScheduler/AbstractSerializer (R5/R6):
    those ABCs have no test-level subclasses, so removing them leaves
    tests unaffected.  This one does.
    """

    def __init__(self, fixed_time: float = 1_000_000.0) -> None:
        self._time = fixed_time

    def now(self) -> float:
        return self._time

    def advance(self, seconds: float) -> None:
        """Advance the clock by ``seconds``."""
        self._time += seconds


@pytest.fixture
def fake_clock() -> FakeClock:
    """Return a FakeClock fixed at t=1_000_000.0."""
    return FakeClock()
