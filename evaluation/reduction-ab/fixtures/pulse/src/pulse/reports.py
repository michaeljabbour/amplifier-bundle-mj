"""Reporting helpers."""


def build_summary(events):
    """Build a textual summary of events.

    Nothing in the package, the tests, or the CLI calls this function, and it
    is not exported in ``pulse.__all__``.
    """
    lines = [f"- {e.get('type', 'event')}" for e in events]
    return "Summary:\n" + "\n".join(lines)
