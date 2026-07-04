"""Legacy runner — superseded implementation, never imported anywhere (R1).

R1 (REMOVABLE): This entire module is safe to delete.  No other module
imports it; it has no callers.  It is kept as a graveyard artefact.
"""

from __future__ import annotations


class LegacyRunner:
    """Original job runner, superseded by runner.Runner.

    R1: Never imported.  Has no callers anywhere in the codebase.
    """

    # Old implementation v1 — commented-out graveyard (R10)
    # def _old_dispatch_v0(self, job_type, payload):
    #     if job_type == "email":
    #         return {"sent": True, "to": payload.get("to")}
    #     elif job_type == "cleanup":
    #         return {"cleaned": True, "items": payload.get("items", [])}
    #     elif job_type == "report":
    #         rows = payload.get("rows", [])
    #         return {"report": "\n".join(str(r) for r in rows)}
    #     elif job_type == "export":
    #         return {"exported": True, "format": payload.get("format", "csv")}
    #     elif job_type == "import":
    #         return {"imported": True, "count": len(payload.get("data", []))}
    #     else:
    #         raise ValueError(f"Unknown legacy job type: {job_type}")
    #     # Never reached but kept for symmetry
    #     return {}

    def run(self, job_id: str, payload: dict) -> dict:
        return {"job_id": job_id, "status": "done", "legacy": True}

    def _dispatch(self, job_type: str, payload: dict) -> dict:
        dispatch = {
            "email": lambda p: {"sent": True},
            "cleanup": lambda p: {"cleaned": True},
        }
        fn = dispatch.get(job_type)
        if fn is None:
            raise ValueError(f"Unknown job type: {job_type!r}")
        return fn(payload)
