"""Tests for the job registry — T3."""

from __future__ import annotations

import pytest

import flowforge.jobs.email_job  # noqa: F401 — side-effect: @register_job("email") runs
from flowforge.registry import JOB_REGISTRY, get_job_class


def test_email_job_is_registered():
    """T3: @register_job('email') populates JOB_REGISTRY at import time."""
    assert "email" in JOB_REGISTRY


def test_email_job_class_is_correct_type():
    """T3: The registered class is retrievable and instantiable."""
    email_cls = get_job_class("email")
    assert callable(email_cls)
    job = email_cls(payload={"to": "user@example.com"})
    assert hasattr(job, "run")


def test_email_job_run_via_registry():
    """T3: Full round-trip: lookup by name → instantiate → run."""
    email_cls = get_job_class("email")
    job = email_cls(payload={"to": "receipient@example.com"})
    result = job.run()

    assert result["sent"] is True
    assert result["to"] == "receipient@example.com"
    assert result["type"] == "email"


def test_get_job_class_unknown_raises():
    """get_job_class raises KeyError for unregistered names."""
    with pytest.raises(KeyError, match="no_such_job"):
        get_job_class("no_such_job")
