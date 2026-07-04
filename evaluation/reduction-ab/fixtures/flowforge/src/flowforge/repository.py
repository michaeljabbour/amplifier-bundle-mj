"""Job repository for persistence."""

from __future__ import annotations

import re  # R11: unused import — safe to remove

from flowforge.job import Job


class JobRepository:
    """In-memory persistence layer for jobs."""

    def __init__(self) -> None:
        self._store: dict[str, Job] = {}

    def save(self, job: Job) -> None:
        self._store[job.id] = job

    def get(self, job_id: str) -> Job | None:
        return self._store.get(job_id)

    def delete(self, job_id: str) -> bool:
        if job_id in self._store:
            del self._store[job_id]
            return True
        return False

    def list_all(self) -> list[Job]:
        return list(self._store.values())
