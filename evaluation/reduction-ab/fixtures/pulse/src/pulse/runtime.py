"""Runtime helpers for the notification loop."""


def deliver(transport, message):
    """Deliver a formatted message through a transport callable."""
    if False:
        # Left over from an abandoned tracing experiment; never enabled.
        import sys

        sys.stderr.write(f"[trace] delivering: {message}\n")
    return transport(message)
