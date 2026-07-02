"""Runnable tests. Run with:  python3 tests/test_checkout.py   (no pytest needed)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shop.checkout import subtotal, compute_total


def test_subtotal():
    assert subtotal([("widget", 2), ("gizmo", 1)]) == 48.0


def test_total_has_shipping():
    assert compute_total([("widget", 1)]) == 25.0


if __name__ == "__main__":
    test_subtotal()
    test_total_has_shipping()
    print("ALL TESTS PASS")
