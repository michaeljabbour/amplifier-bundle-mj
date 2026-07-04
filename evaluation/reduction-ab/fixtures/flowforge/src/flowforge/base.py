"""BaseJob ABC — load-bearing: runtime uses __subclasses__() to enumerate types.

T4: This ABC is NOT collapsible like R5/R6 (BaseScheduler, AbstractSerializer).
``discover_job_classes()`` relies on ``BaseJob.__subclasses__()`` at runtime;
removing BaseJob or detaching EmailJob from it breaks that enumeration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseJob(ABC):
    """Abstract base for all concrete job types.

    T4 (LOAD-BEARING): Runtime code calls ``BaseJob.__subclasses__()`` via
    ``discover_job_classes()`` to enumerate available job implementations.
    This ABC earns its keep — it is NOT the same as BaseScheduler (R5) or
    AbstractSerializer (R6), which have no such runtime introspection.
    """

    @abstractmethod
    def run(self) -> dict:
        """Execute the job and return a result dict."""
        ...


def discover_job_classes() -> dict[str, type]:
    """Enumerate all loaded BaseJob subclasses by name.

    T4: Called at runtime. Uses ``BaseJob.__subclasses__()`` — if BaseJob is
    removed, or a concrete class is detached from its MRO, this breaks.

    Note: only classes that have been *imported* appear here. Import the
    jobs package before calling if you need a complete registry.
    """
    return {cls.__name__: cls for cls in BaseJob.__subclasses__()}
