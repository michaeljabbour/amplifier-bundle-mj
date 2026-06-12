"""Shared test fixtures."""

from pulse.cache import Cache


class FakeCache(Cache):
    """In-memory test double injected through the Cache interface."""

    def __init__(self):
        self._seen = set()

    def seen(self, key):
        return key in self._seen

    def remember(self, key):
        self._seen.add(key)
