"""A todo is a plain dict: {"id": int, "title": str, "done": bool}."""


def new_todo(todo_id, title):
    return {"id": todo_id, "title": title, "done": False}
