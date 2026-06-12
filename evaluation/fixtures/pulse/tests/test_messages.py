from pulse.messages import format_message


def test_format_message_basic():
    assert format_message({"title": "Deploy", "body": "done"}) == "Deploy: done"


def test_format_message_defaults():
    assert format_message({}) == "untitled:"
