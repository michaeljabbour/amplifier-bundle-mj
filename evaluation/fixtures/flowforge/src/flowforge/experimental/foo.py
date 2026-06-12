"""Experimental batch runner — never imported anywhere (R2).

R2 (REMOVABLE): Part of the ``experimental`` package; no callers exist.
"""

from __future__ import annotations


def experimental_batch_run(jobs: list) -> list[dict]:
    """Experimental batch execution — not yet integrated into the main pipeline."""
    return [{"job": j, "status": "experimental"} for j in jobs]


# Old experimental prototype — kept as a graveyard comment (R10)
# class ExperimentalParallelRunner:
#     """Attempted parallel execution engine — abandoned due to race conditions."""
#
#     def __init__(self, workers: int = 4):
#         self._workers = workers
#         self._queue: list = []
#         self._results: dict = {}
#         self._lock = None  # threading.Lock() placeholder
#
#     def enqueue(self, job_id: str, payload: dict) -> None:
#         self._queue.append((job_id, payload))
#
#     def drain(self) -> list[dict]:
#         results = []
#         for job_id, payload in self._queue:
#             results.append({"job_id": job_id, "result": "ok"})
#         self._queue.clear()
#         return results
#
#     def _worker_loop(self) -> None:
#         while self._queue:
#             job_id, payload = self._queue.pop(0)
#             self._results[job_id] = experimental_batch_run([payload])
