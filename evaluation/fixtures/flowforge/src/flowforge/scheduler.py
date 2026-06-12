"""Scheduler — single-implementation ABC, never subclassed elsewhere (R5).

BaseScheduler + SimpleScheduler look like T7 (Clock + SystemClock) but are NOT
load-bearing: no test injects a fake scheduler, there is no DI, and the pair
is never used outside this module.  Safe to collapse to a plain class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone


class BaseScheduler(ABC):
    """Abstract base for job schedulers.

    R5 (REMOVABLE): Only one concrete implementation (SimpleScheduler)
    exists.  No tests inject a fake scheduler — unlike Clock/FakeClock (T7),
    there is no test-level inheritance here.  No DI.  The ABC buys nothing;
    collapse to a plain class.
    """

    @abstractmethod
    def schedule(self, job_id: str, run_at: datetime) -> None:
        """Schedule a job to run at ``run_at``."""
        ...

    @abstractmethod
    def get_pending(self) -> list[str]:
        """Return IDs of jobs whose scheduled time has passed."""
        ...


class SimpleScheduler(BaseScheduler):
    """Trivial in-memory scheduler."""

    def __init__(self) -> None:
        self._pending: list[tuple[str, datetime]] = []

    def schedule(self, job_id: str, run_at: datetime) -> None:
        self._pending.append((job_id, run_at))

    def get_pending(self) -> list[str]:
        now = datetime.now(tz=timezone.utc)
        return [jid for jid, run_at in self._pending if run_at <= now]
