from pulse.formatters import PlainFormatter


def test_plain_formatter_renders_str():
    assert PlainFormatter().render(123) == "123"
    assert PlainFormatter().render("hi") == "hi"
