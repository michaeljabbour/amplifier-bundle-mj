"""Tests for clock injection — T7."""

from __future__ import annotations

from flowforge.clock import Clock, SystemClock
from flowforge.job import Job
from flowforge.runner import Runner
from flowforge.step import Step


def test_fake_clock_provides_deterministic_time(fake_clock):
    """T7: FakeClock injects a fixed timestamp into Runner.execute()."""
    runner = Runner(clock=fake_clock)
    job = Job(id="j1", type="run", kind="run")
    steps = [Step(type="run", job_id="j1")]

    result = runner.execute(job, steps)

    assert result["timestamp"] == fake_clock.now()
    assert result["timestamp"] == 1_000_000.0


def test_fake_clock_is_clock_instance(fake_clock):
    """T7: FakeClock correctly inherits from the Clock ABC."""
    assert isinstance(fake_clock, Clock)


def test_fake_clock_advance(fake_clock):
    """FakeClock.advance() increments the stored time."""
    t0 = fake_clock.now()
    fake_clock.advance(60.0)
    assert fake_clock.now() == t0 + 60.0


def test_system_clock_implements_clock():
    """SystemClock satisfies the Clock interface."""
    sc = SystemClock()
    assert isinstance(sc, Clock)
    assert sc.now() > 0


def test_runner_uses_default_clock_when_none_given():
    """Runner defaults to SystemClock when no clock is injected."""
    runner = Runner()
    job = Job(id="j2", type="run", kind="run")
    steps = [Step(type="run", job_id="j2")]
    result = runner.execute(job, steps)
    # SystemClock returns a real Unix timestamp (> 0)
    assert result["timestamp"] > 0
