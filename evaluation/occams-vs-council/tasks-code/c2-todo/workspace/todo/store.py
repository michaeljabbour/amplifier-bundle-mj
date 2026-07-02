"""JSON file persistence for the todo list."""
import json
import os


def load(path):
    """Return the list of todos stored at `path` (empty list if absent)."""
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save(path, todos):
    """Write `todos` (a list of dicts) to `path` as JSON."""
    with open(path, "w") as f:
        json.dump(todos, f, indent=2)
