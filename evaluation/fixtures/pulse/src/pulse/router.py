"""Event routing via dynamic handler dispatch."""


class EventRouter:
    """Routes events to ``handle_<type>`` methods by name.

    Handlers are invoked via ``getattr`` using the event's ``type`` field, so
    they have no static call sites anywhere in the codebase.
    """

    def __init__(self):
        self.delivered = []

    def dispatch(self, event):
        handler_name = "handle_" + event["type"]
        handler = getattr(self, handler_name, self.handle_unknown)
        return handler(event)

    def handle_ping(self, event):
        self.delivered.append(("ping", event.get("body", "")))
        return "pong"

    def handle_alert(self, event):
        self.delivered.append(("alert", event.get("body", "")))
        return "alerted"

    def handle_unknown(self, event):
        return "ignored"
