"""Tests for CachingStore memoisation — T8."""

from __future__ import annotations

from flowforge.store import CachingStore, Store


def test_caching_store_calls_backing_exactly_once():
    """T8: Two reads for the same key call backing.expensive_fetch only once.

    Naively inlining CachingStore (calling the backing store directly) raises
    _fetch_count to 2, failing the == 1 assertion.
    """
    backing = Store()
    cache = CachingStore(backing)

    val1 = cache.get("foo")
    val2 = cache.get("foo")  # cache hit — backing not called again

    assert val1 == val2
    assert backing._fetch_count == 1  # T8: impure load-bearing assertion


def test_caching_store_different_keys_each_fetched_once():
    """Each distinct key triggers exactly one backing fetch."""
    backing = Store()
    cache = CachingStore(backing)

    cache.get("a")
    cache.get("b")
    cache.get("a")  # cache hit for 'a'
    cache.get("b")  # cache hit for 'b'

    assert backing._fetch_count == 2  # 'a' and 'b', each once


def test_caching_store_returns_consistent_values():
    """CachingStore returns the same value on repeated reads."""
    backing = Store()
    backing.set("key", "stored_value")
    cache = CachingStore(backing)

    assert cache.get("key") == "stored_value"
    assert cache.get("key") == "stored_value"


def test_store_fetch_count_tracks_all_direct_calls():
    """Store._fetch_count increments on every expensive_fetch call."""
    store = Store()
    store.expensive_fetch("x")
    store.expensive_fetch("x")
    store.expensive_fetch("y")
    assert store._fetch_count == 3
