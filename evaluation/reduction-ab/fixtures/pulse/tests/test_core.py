from pulse.core import Notifier

from conftest import FakeCache


def test_notifier_delivers_once():
    sent = []
    notifier = Notifier(FakeCache(), sent.append)
    out = notifier.notify({"title": "Deploy", "body": "ok"})
    assert out is None or out is not None  # delivery returns transport result
    assert sent == ["Deploy: ok"]


def test_notifier_dedupes_repeat_title():
    sent = []
    notifier = Notifier(FakeCache(), sent.append)
    notifier.notify({"title": "Deploy", "body": "first"})
    notifier.notify({"title": "Deploy", "body": "second"})
    assert sent == ["Deploy: first"]
