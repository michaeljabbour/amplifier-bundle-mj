"""Job runner with dynamic step dispatch.

T1a (LOAD-BEARING):  _handle_retry — invoked only via getattr; zero static callers.
T1b (UNCOVERED trap): _handle_skip — same mechanism, no test exercises "skip" steps.
R13 (REMOVABLE):     EventBus emission on job completion; could be a direct call.
"""

from __future__ import annotations

import logging  # R11: unused import — safe to remove
from typing import Any

from flowforge.clock import Clock, SystemClock
from flowforge.events import _bus
from flowforge.job import Job
from flowforge.step import Step

_DEBUG = False  # R9: always False; the if-block below is a dead branch


# R14: duplicates utils.format_result verbatim — the canonical lives in utils.py
def _format_result(result: dict) -> str:
    return f"Result({result})"


class Runner:
    """Executes jobs as ordered sequences of typed steps.

    Step handlers are resolved dynamically:
        handler = getattr(self, f"_handle_{step.type}", None)

    This makes ``_handle_retry`` (T1a) and ``_handle_skip`` (T1b) invisible
    to static analysis — they look like dead methods but are reachable at
    runtime by any step whose ``type`` matches the suffix.
    """

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock: Clock = clock if clock is not None else SystemClock()

    def execute(self, job: Job, steps: list[Step], extra: Any = None) -> dict:  # R8: extra unused
        """Run all steps for ``job`` and return a result summary.

        ``extra`` is accepted but never read (R8).
        """
        if _DEBUG:  # R9: dead branch
            print(f"[DEBUG] Executing job {job.id!r}")

        results = []
        for step in steps:
            result = self.run_step(step)
            results.append(result)

        # R13: EventBus fires in exactly one place; could be a direct callback
        _bus.emit("job.completed", {"job_id": job.id, "steps": len(steps)})

        return {
            "job_id": job.id,
            "results": results,
            "timestamp": self._clock.now(),
            "status": "completed",
        }

    def run_step(self, step: Step) -> dict:
        """Dispatch ``step`` to the matching ``_handle_<type>`` method.

        Dynamic attribute lookup — static callers of the individual handlers
        do not exist.  Removing a handler silently breaks any step of that
        type at runtime.
        """
        handler_name = f"_handle_{step.type}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            raise ValueError(
                f"Runner has no handler for step type {step.type!r}. "
                f"Add a _handle_{step.type}(self, step) -> dict method."
            )
        return handler(step)

    # ------------------------------------------------------------------
    # Step handlers — only reachable via run_step() dynamic dispatch
    # ------------------------------------------------------------------

    def _handle_run(self, step: Step) -> dict:
        """Handle a normal execution step."""
        return {
            "step_type": "run",
            "job_id": step.job_id,
            "status": "completed",
        }

    def _handle_retry(self, step: Step) -> dict:
        """Handle a retry step.

        T1a (LOAD-BEARING): zero static callers; reached only via
        ``run_step`` when ``step.type == "retry"``.  A test exercises this
        path — removing this method raises ValueError at runtime.
        """
        max_attempts = step.params.get("max_attempts", 3)
        return {
            "step_type": "retry",
            "job_id": step.job_id,
            "retried": True,
            "max_attempts": max_attempts,
        }

    def _handle_skip(self, step: Step) -> dict:
        """Handle a skip step.

        T1b (UNCOVERED): same dynamic-dispatch mechanism as _handle_retry,
        but NO test exercises a "skip" step.  Removing this keeps the suite
        green — but it silently removes a valid step type from the contract.
        """
        return {
            "step_type": "skip",
            "job_id": step.job_id,
            "skipped": True,
        }
