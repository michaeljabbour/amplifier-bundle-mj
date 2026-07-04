"""Storage layer with a caching wrapper.

T8 (LOAD-BEARING): CachingStore is IMPURE — it memoises expensive_fetch so the
backing store is called exactly once per key, regardless of how many reads occur.
Collapsing the wrapper (calling the backing store directly) changes the call count
from 1 to N, failing the test that asserts backing._fetch_count == 1.
"""

from __future__ import annotations


class Store:
    """Simple key-value store with an intentionally expensive fetch operation."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self._fetch_count: int = 0  # observable side-effect counter

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def expensive_fetch(self, key: str) -> str:
        """Fetch a value — increments the observable call counter."""
        self._fetch_count += 1
        return self._data.get(key, f"value_for_{key}")


class CachingStore:
    """Wraps Store with a memoisation layer.

    T8 (LOAD-BEARING): The cache makes ``expensive_fetch`` on the backing
    store be called exactly once per key, no matter how many reads happen.
    This is impure behaviour: the wrapper changes observable state (fetch count)
    relative to a transparent passthrough.

    Naively collapsing this by removing the cache and calling the backing
    store directly causes each ``get()`` call to increment ``_fetch_count``,
    turning the test assertion ``_fetch_count == 1`` into a failure.
    """

    def __init__(self, backing: Store) -> None:
        self._backing = backing
        self._cache: dict[str, str] = {}

    def get(self, key: str) -> str:
        """Return the value for ``key``, fetching from backing exactly once."""
        if key not in self._cache:
            self._cache[key] = self._backing.expensive_fetch(key)
        return self._cache[key]
