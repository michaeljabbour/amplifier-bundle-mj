"""Job data model.

R12: Job._status_cache mirrors .status and is reconciled by hand in set_status.
T5:  Job.kind persists and is the authoritative source in from_dict.
"""

from __future__ import annotations

import os  # R11: unused import — safe to remove
from dataclasses import dataclass, field
from typing import Any

_DEBUG = False  # R9: never True; the if-branch below is a dead branch


@dataclass
class Job:
    """Represents a unit of work in the workflow system.

    ``type`` and ``kind`` both hold the job-type string.  They are populated
    identically on construction.  On *restore* (``from_dict``), ``kind`` is
    the authoritative source used to reconstruct ``type`` — removing ``kind``
    from the serialised form or from the class definition breaks round-trips
    (T5).

    ``_status_cache`` (R12) is redundant state that mirrors ``status``; it is
    reconciled by hand in ``set_status``.  It is safe to derive or delete.
    """

    id: str
    type: str
    kind: str  # T5: persisted separately; read in from_dict to reconstruct type
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    status: str = "pending"
    # R12: mirrors .status; reconciled by hand; derivable — safe to remove
    _status_cache: str = field(default="pending", init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._status_cache = self.status  # R12: initial sync

    # ------------------------------------------------------------------
    # Status management
    # ------------------------------------------------------------------

    def set_status(self, new_status: str) -> None:
        """Update job status."""
        if _DEBUG:  # R9: dead branch — _DEBUG is always False
            print(f"[DEBUG] status {self.status!r} → {new_status!r}")
        self.status = new_status
        self._status_cache = new_status  # R12: redundant reconciliation

    def get_effective_status(self) -> str:
        """Return current status (always equal to .status via the cache)."""
        return self._status_cache  # R12

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize job to a plain dictionary.

        ``kind`` MUST be included here; ``from_dict`` reads it to reconstruct
        the object (T5).
        """
        # Old v1 serialiser — kept as a graveyard comment (R10)
        # result = {}
        # result["id"]      = self.id
        # result["type"]    = self.type
        # result["kind"]    = self.kind
        # result["payload"] = self.payload
        # result["priority"] = self.priority
        # result["status"]  = self.status
        # for k, v in self.payload.items():
        #     result["payload_" + k] = str(v)
        # result["_v"] = 1
        # return result
        return {
            "id": self.id,
            "type": self.type,
            "kind": self.kind,  # T5: load-bearing in from_dict
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        """Restore a Job from a serialised dictionary.

        T5 (LOAD-BEARING): ``kind`` is the authoritative field here.
        ``type`` is reconstructed from it.  If ``kind`` is absent in
        ``data`` (because it was stripped from ``to_dict``), this raises
        ``KeyError``, breaking the persist→restore round-trip test.
        """
        if False:  # R9: dead branch — legacy guard that never executes
            raise NotImplementedError("from_dict not available in legacy mode")
        kind = data["kind"]  # T5: key lookup — fails if kind was removed from to_dict
        return cls(
            id=data["id"],
            type=kind,  # reconstructed from kind, not from data["type"]
            kind=kind,
            payload=data.get("payload", {}),
            priority=data.get("priority", 5),
            status=data.get("status", "pending"),
        )
