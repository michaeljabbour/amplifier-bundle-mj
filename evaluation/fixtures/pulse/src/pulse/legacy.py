"""Legacy compatibility helpers."""


def normalize_type(raw):
    """Normalize a raw event type string to lowercase."""
    return (raw or "").strip().lower()


# --- old v1 implementation, kept around "just in case" -------------------
# def normalize_type(raw):
#     mapping = {"PING": "ping", "Alert": "alert", "warn": "warning"}
#     if raw in mapping:
#         return mapping[raw]
#     result = ""
#     for ch in raw:
#         if ch.isupper():
#             result += ch.lower()
#         else:
#             result += ch
#     return result.strip()
#
# def legacy_dispatch(router, event):
#     # superseded by EventRouter.dispatch
#     handler = getattr(router, "on_" + event["type"], None)
#     if handler is None:
#         raise KeyError(event["type"])
#     return handler(event)
# -------------------------------------------------------------------------
