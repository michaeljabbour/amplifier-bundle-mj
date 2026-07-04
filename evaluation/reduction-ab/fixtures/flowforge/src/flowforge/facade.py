"""Runner facade — pure passthrough to Runner (R4).

Every method forwards 1:1 with zero added logic.  Callers can use Runner
directly; this class is collapsible.
"""

from __future__ import annotations

from typing import Any

from flowforge.job import Job
from flowforge.runner import Runner
from flowforge.step import Step


class RunnerFacade:
    """Delegates all calls to Runner without adding behaviour.

    R4 (REMOVABLE): Pure passthrough — zero added logic.  Every method is
    exactly one line: ``return self._runner.method(...)``.  Safe to collapse
    callers directly onto Runner.
    """

    def __init__(self, runner: Runner | None = None) -> None:
        self._runner = runner or Runner()

    def execute(self, job: Job, steps: list[Step], extra: Any = None) -> dict:
        return self._runner.execute(job, steps, extra)

    def run_step(self, step: Step) -> dict:
        return self._runner.run_step(step)
