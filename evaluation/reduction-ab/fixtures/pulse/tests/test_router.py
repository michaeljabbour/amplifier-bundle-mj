from pulse.router import EventRouter


def test_dispatch_ping():
    router = EventRouter()
    assert router.dispatch({"type": "ping", "body": "x"}) == "pong"
    assert ("ping", "x") in router.delivered


def test_dispatch_alert():
    router = EventRouter()
    assert router.dispatch({"type": "alert", "body": "fire"}) == "alerted"


def test_dispatch_unknown():
    router = EventRouter()
    assert router.dispatch({"type": "nope"}) == "ignored"
