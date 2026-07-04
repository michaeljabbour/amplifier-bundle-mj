"""Tests for Runner: end-to-end run and T1a (retry step)."""

from __future__ import annotations

import pytest

from flowforge.job import Job
from flowforge.runner import Runner
from flowforge.step import Step


def test_end_to_end_run(fake_clock):
    """Normal end-to-end job execution through Runner."""
    runner = Runner(clock=fake_clock)
    job = Job(id="j1", type="run", kind="run", payload={"key": "value"})
    steps = [Step(type="run", job_id="j1")]

    result = runner.execute(job, steps)

    assert result["job_id"] == "j1"
    assert result["status"] == "completed"
    assert len(result["results"]) == 1
    assert result["results"][0]["step_type"] == "run"
    assert result["results"][0]["status"] == "completed"


def test_end_to_end_multiple_steps(fake_clock):
    """Multiple steps are all executed in order."""
    runner = Runner(clock=fake_clock)
    job = Job(id="j2", type="run", kind="run")
    steps = [
        Step(type="run", job_id="j2"),
        Step(type="run", job_id="j2"),
    ]

    result = runner.execute(job, steps)

    assert result["job_id"] == "j2"
    assert len(result["results"]) == 2


def test_retry_step(fake_clock):
    """T1a: _handle_retry is only reachable via dynamic dispatch in run_step()."""
    runner = Runner(clock=fake_clock)
    job = Job(id="j3", type="retry", kind="retry")
    steps = [Step(type="retry", job_id="j3", params={"max_attempts": 5})]

    result = runner.execute(job, steps)

    assert result["status"] == "completed"
    retry_result = result["results"][0]
    assert retry_result["step_type"] == "retry"
    assert retry_result["retried"] is True
    assert retry_result["max_attempts"] == 5


def test_retry_step_default_max_attempts(fake_clock):
    """_handle_retry defaults max_attempts to 3 when not specified."""
    runner = Runner(clock=fake_clock)
    job = Job(id="j4", type="retry", kind="retry")
    steps = [Step(type="retry", job_id="j4")]

    result = runner.execute(job, steps)

    assert result["results"][0]["max_attempts"] == 3


def test_unknown_step_type_raises():
    """Runner raises ValueError for an unregistered step type."""
    runner = Runner()
    step = Step(type="nonexistent_type", job_id="jX")
    with pytest.raises(ValueError, match="nonexistent_type"):
        runner.run_step(step)


def test_runner_timestamp_comes_from_clock(fake_clock):
    """The result timestamp is taken from the injected clock (supports T7)."""
    runner = Runner(clock=fake_clock)
    job = Job(id="j5", type="run", kind="run")
    steps = [Step(type="run", job_id="j5")]

    result = runner.execute(job, steps)

    assert result["timestamp"] == fake_clock.now()
    assert result["timestamp"] == 1_000_000.0
