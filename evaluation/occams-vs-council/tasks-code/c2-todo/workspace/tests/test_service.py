"""Runnable tests. Run with:  python3 tests/test_service.py   (no pytest needed)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from todo import service


def test_add_assigns_incrementing_ids():
    todos = []
    a = service.add(todos, "one")
    b = service.add(todos, "two")
    assert a["id"] == 1 and b["id"] == 2
    assert len(todos) == 2


def test_complete_marks_done():
    todos = []
    service.add(todos, "task")
    service.complete(todos, 1)
    assert todos[0]["done"] is True


def test_list_returns_all():
    todos = []
    service.add(todos, "a")
    service.add(todos, "b")
    assert len(service.list_todos(todos)) == 2


if __name__ == "__main__":
    test_add_assigns_incrementing_ids()
    test_complete_marks_done()
    test_list_returns_all()
    print("ALL TESTS PASS")
