"""FlowForge: a job/workflow runner.

Public surface consumed by downstream tooling.
"""

from flowforge.job import Job
from flowforge.runner import Runner


def format_report(results: list[dict]) -> str:
    """Format job results as a human-readable report.

    T6 (UNCOVERED): exported in __all__; no in-repo callers; consumed by
    hypothetical downstream tooling. Removing it keeps the test suite green
    but silently removes a public API commitment.
    """
    lines = ["=== FlowForge Report ==="]
    for r in results:
        lines.append(f"  job={r.get('job_id', '?')}  status={r.get('status', '?')}")
    return "\n".join(lines)


__all__ = [
    "Runner",
    "Job",
    "format_report",  # T6: public API, zero in-repo callers
]
