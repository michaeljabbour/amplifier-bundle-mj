"""Email job — registered via @register_job('email') at import time (T3).

T3 (LOAD-BEARING): The @register_job decorator populates JOB_REGISTRY["email"]
when this module is first imported.  Static analysis sees no callers for
EmailJob; the registry is the only runtime dispatch path.  Removing the
decorator leaves the registry empty and breaks the test.
"""

from __future__ import annotations

from flowforge.base import BaseJob
from flowforge.registry import register_job


@register_job("email")  # T3: populates JOB_REGISTRY at import time
class EmailJob(BaseJob):
    """Sends an email.

    T3: Only reachable via ``get_job_class("email")``.  Static callers: none.
    T4: Subclasses BaseJob — appears in ``BaseJob.__subclasses__()`` once
        this module is imported.  Removing the MRO relationship breaks
        discover_job_classes().
    """

    def __init__(self, payload: dict | None = None) -> None:
        self.payload: dict = payload or {}

    def run(self) -> dict:
        return {
            "type": "email",
            "sent": True,
            "to": self.payload.get("to", "unknown"),
        }
