"""Cleanup job — registered ONLY via pyproject.toml entry point (T2).

T2 (UNCOVERED): No in-repo Python file imports or instantiates CleanupJob.
No test exercises it.  The only declaration is in pyproject.toml:

    [project.entry-points."flowforge.jobs"]
    cleanup = "flowforge.jobs.cleanup_job:CleanupJob"

A grep of *.py files finds nothing; only pyproject.toml reveals it matters.
Removing it keeps the test suite green but silently removes a public entry
point advertised to external tooling.
"""

from __future__ import annotations

from flowforge.base import BaseJob


class CleanupJob(BaseJob):
    """Performs system cleanup tasks.

    T2: Registered only via the ``flowforge.jobs`` entry-point group in
    pyproject.toml.  Zero in-repo callers; zero test coverage.
    """

    def run(self) -> dict:
        return {"type": "cleanup", "cleaned": True}
