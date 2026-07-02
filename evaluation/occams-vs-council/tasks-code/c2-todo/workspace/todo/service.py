"""Core todo operations on an in-memory list of todo dicts."""
from todo.models import new_todo


def add(todos, title):
    todo_id = max((t["id"] for t in todos), default=0) + 1
    todo = new_todo(todo_id, title)
    todos.append(todo)
    return todo


def list_todos(todos):
    return list(todos)


def complete(todos, todo_id):
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            return t
    raise KeyError(f"No todo with id {todo_id}")
