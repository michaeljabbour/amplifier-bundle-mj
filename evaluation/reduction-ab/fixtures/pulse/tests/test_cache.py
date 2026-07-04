from pulse.cache import Dedupe

from conftest import FakeCache


def test_dedupe_suppresses_second_delivery():
    dedupe = Dedupe(FakeCache())
    assert dedupe.allow("k1") is True
    assert dedupe.allow("k1") is False


def test_dedupe_allows_distinct_keys():
    dedupe = Dedupe(FakeCache())
    assert dedupe.allow("a") is True
    assert dedupe.allow("b") is True
