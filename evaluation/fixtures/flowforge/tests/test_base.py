"""Tests for BaseJob subclass enumeration — T4."""

from __future__ import annotations

import flowforge.jobs.email_job  # noqa: F401 — ensures EmailJob is loaded + registered
from flowforge.base import BaseJob, discover_job_classes


def test_discover_job_classes_includes_email():
    """T4: discover_job_classes() uses BaseJob.__subclasses__() at runtime.

    Removing BaseJob or detaching EmailJob from its MRO returns an empty dict
    (or raises ImportError), failing this assertion.
    """
    types = discover_job_classes()
    assert "EmailJob" in types


def test_basejob_subclasses_nonempty():
    """T4: After importing email_job, BaseJob.__subclasses__() is non-empty."""
    subclasses = BaseJob.__subclasses__()
    names = {cls.__name__ for cls in subclasses}
    assert "EmailJob" in names


def test_discovered_class_is_instantiable():
    """T4: The discovered class can be instantiated and run."""
    types = discover_job_classes()
    email_cls = types["EmailJob"]
    job = email_cls(payload={"to": "test@example.com"})
    result = job.run()
    assert result["sent"] is True
