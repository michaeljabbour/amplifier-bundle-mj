"""Tests for priority validation — T9."""

from __future__ import annotations

from flowforge.validate import validate_priority


def test_priority_clamped_high():
    """T9: priority=99 is clamped to 9."""
    assert validate_priority(99) == 9


def test_priority_clamped_at_ten():
    """T9: priority=10 (just above max) is clamped to 9."""
    assert validate_priority(10) == 9


def test_priority_clamped_low():
    """T9: negative priorities are clamped to 0."""
    assert validate_priority(-5) == 0
    assert validate_priority(-1) == 0


def test_priority_in_range_unchanged():
    """Priorities in [0, 9] pass through unchanged."""
    for p in range(10):
        assert validate_priority(p) == p


def test_priority_boundary_values():
    """Exact boundary values 0 and 9 are not modified."""
    assert validate_priority(0) == 0
    assert validate_priority(9) == 9
