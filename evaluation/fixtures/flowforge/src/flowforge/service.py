"""Job service — pure passthrough to JobRepository (R3).

Every method forwards 1:1 to the underlying repository with zero added
logic.  This layer is collapsible: callers can use JobRepository directly.
"""

from __future__ import annotations

from flowforge.config import Config
from flowforge.job import Job
from flowforge.repository import JobRepository


class JobService:
    """Forwards all job operations to JobRepository without modification.

    R3 (REMOVABLE): Pure passthrough — zero added logic per method.
    All four of Config's *used* fields are read here; the remaining 18
    declared in Config are never accessed anywhere (R7).
    """

    def __init__(
        self,
        repository: JobRepository | None = None,
        config: Config | None = None,
    ) -> None:
        self._repo = repository or JobRepository()
        cfg = config or Config()
        # R7: only these 4 of Config's 22 fields are read anywhere
        self._max_retries = cfg.max_retries
        self._timeout = cfg.timeout_seconds
        self._queue = cfg.queue_name
        self._log_level = cfg.log_level

    def save(self, job: Job) -> None:
        self._repo.save(job)

    def get(self, job_id: str) -> Job | None:
        return self._repo.get(job_id)

    def delete(self, job_id: str) -> bool:
        return self._repo.delete(job_id)

    def list_all(self) -> list[Job]:
        return self._repo.list_all()
