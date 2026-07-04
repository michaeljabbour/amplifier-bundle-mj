"""Public API surface.

``format_response`` is part of the package's public, exported API (listed in
``pulse.__all__``). It has no in-repo callers because it is consumed by
downstream packages that depend on ``pulse``.
"""


def format_response(status, detail=""):
    """Format a public API response envelope."""
    return {"status": status, "detail": detail}
