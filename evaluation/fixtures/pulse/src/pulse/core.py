"""Core notification flow wiring the pieces together."""

from pulse.cache import Dedupe
from pulse.formatters import PlainFormatter
from pulse.legacy import normalize_type
from pulse.messages import format_message
from pulse.runtime import deliver


class Notifier:
    def __init__(self, cache, transport):
        self._dedupe = Dedupe(cache)
        self._formatter = PlainFormatter()
        self._transport = transport

    def notify(self, payload):
        key = normalize_type(payload.get("title", ""))
        if not self._dedupe.allow(key):
            return None
        rendered = self._formatter.render(format_message(payload))
        return deliver(self._transport, rendered)
