"""Tests for Job data model — T5 (persist→restore round-trip)."""

from __future__ import annotations

from flowforge.job import Job


def test_persist_restore_round_trip():
    """T5: Job.kind is serialised by to_dict and used by from_dict to reconstruct type.

    Removing ``kind`` from to_dict (or from the class) causes from_dict to raise
    KeyError, failing this test.
    """
    original = Job(
        id="j1",
        type="email",
        kind="email",
        payload={"to": "test@example.com"},
        priority=3,
    )

    serialised = original.to_dict()
    restored = Job.from_dict(serialised)

    assert restored.id == original.id
    assert restored.type == original.type
    assert restored.kind == original.kind
    assert restored.payload == original.payload
    assert restored.priority == original.priority
    assert restored.status == original.status


def test_to_dict_contains_kind():
    """T5: kind must appear in to_dict output for the round-trip to work."""
    job = Job(id="j2", type="cleanup", kind="cleanup")
    data = job.to_dict()
    assert "kind" in data
    assert data["kind"] == "cleanup"


def test_from_dict_uses_kind_to_set_type():
    """T5: from_dict sets type from kind, not from the type key."""
    # type key has a different value than kind — from_dict should use kind
    data = {
        "id": "j3",
        "type": "IGNORED",  # this is overwritten by kind
        "kind": "email",
        "payload": {},
        "priority": 5,
        "status": "pending",
    }
    job = Job.from_dict(data)
    assert job.type == "email"  # reconstructed from kind
    assert job.kind == "email"


def test_job_status_update():
    """set_status updates both status and _status_cache (R12)."""
    job = Job(id="j4", type="run", kind="run")
    assert job.status == "pending"
    job.set_status("running")
    assert job.status == "running"
    assert job.get_effective_status() == "running"


def test_job_default_priority():
    """Default priority is 5."""
    job = Job(id="j5", type="run", kind="run")
    assert job.priority == 5
