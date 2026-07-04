"""Step data model for workflow execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Step:
    """A single execution step within a workflow.

    The ``type`` field is used for dynamic dispatch in ``Runner.run_step``.
    Valid built-in types: ``"run"``, ``"retry"``, ``"skip"``.
    """

    type: str
    job_id: str
    params: dict[str, Any] = field(default_factory=dict)
