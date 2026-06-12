"""JobFactory — just calls constructors, adds no logic (R16).

Every factory method is a thin wrapper around the class constructor.
No validation, no defaults beyond the dataclass's own, no transformation.
Callers can instantiate Job and Step directly.
"""

from __future__ import annotations

from typing import Any

from flowforge.job import Job
from flowforge.step import Step


class JobFactory:
    """Factory for Job and Step objects.

    R16 (REMOVABLE): Every method is exactly one statement: a constructor call.
    There is no added logic, no validation, no default enrichment beyond what
    the dataclasses themselves already provide.  Safe to inline at all call
    sites.
    """

    @staticmethod
    def create_job(
        job_id: str,
        job_type: str,
        payload: dict[str, Any] | None = None,
        priority: int = 5,
    ) -> Job:
        return Job(
            id=job_id,
            type=job_type,
            kind=job_type,
            payload=payload or {},
            priority=priority,
        )

    @staticmethod
    def create_step(
        step_type: str,
        job_id: str,
        params: dict[str, Any] | None = None,
    ) -> Step:
        return Step(type=step_type, job_id=job_id, params=params or {})
