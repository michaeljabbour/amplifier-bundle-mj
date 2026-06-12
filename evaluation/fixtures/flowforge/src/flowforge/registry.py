"""Job registry — load-bearing: @register_job populates JOB_REGISTRY at import time.

T3 (LOAD-BEARING): the decorator is the sole mechanism by which named jobs are
registered.  Removing it (or removing registry.py) leaves JOB_REGISTRY empty
and breaks the test that looks up and runs "email".
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

# T3: populated at module-import time by @register_job decorators
JOB_REGISTRY: dict[str, type] = {}


def register_job(name: str) -> Callable[[type[T]], type[T]]:
    """Class decorator that registers a job type under ``name``.

    T3 (LOAD-BEARING): the decorated class is inserted into JOB_REGISTRY when
    the module containing the decorator call is first imported.  Removing this
    decorator from ``email_job.py`` leaves the registry empty; removing
    registry.py entirely breaks the import chain.
    """

    def decorator(cls: type[T]) -> type[T]:
        JOB_REGISTRY[name] = cls  # type: ignore[assignment]
        return cls

    return decorator


def get_job_class(name: str) -> type:
    """Look up a registered job class by name.

    Raises ``KeyError`` if the name is not in the registry.
    """
    if name not in JOB_REGISTRY:
        raise KeyError(f"No job registered under {name!r}. Known jobs: {sorted(JOB_REGISTRY)}")
    return JOB_REGISTRY[name]
