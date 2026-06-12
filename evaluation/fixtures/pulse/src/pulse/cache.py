"""Cache abstraction for delivery deduplication.

Looks structurally identical to ``formatters.py`` (an ABC with a single
concrete implementation), but the abstraction is load-bearing: the test suite
injects a ``FakeCache`` built on this interface, so the base class is the seam
that makes the code testable.
"""

from abc import ABC, abstractmethod


class Cache(ABC):
    @abstractmethod
    def seen(self, key):
        ...

    @abstractmethod
    def remember(self, key):
        ...


class RedisCache(Cache):
    def __init__(self, client):
        self._client = client

    def seen(self, key):
        return bool(self._client.exists(key))

    def remember(self, key):
        self._client.set(key, "1")


class Dedupe:
    """Uses a Cache to suppress duplicate deliveries."""

    def __init__(self, cache):
        self._cache = cache

    def allow(self, key):
        if self._cache.seen(key):
            return False
        self._cache.remember(key)
        return True
