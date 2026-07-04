"""Message formatting helpers."""


def format_message(payload, verbose=False):
    """Render a payload dict into a human-readable notification line.

    The ``verbose`` flag is accepted but never consulted anywhere in the
    codebase or its callers.
    """
    title = payload.get("title", "untitled")
    body = payload.get("body", "")
    return f"{title}: {body}".strip()
