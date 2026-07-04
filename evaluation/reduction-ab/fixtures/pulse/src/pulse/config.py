"""Configuration defaults."""

import json
import os

DEFAULT_CHANNEL = "general"


def channel_from_env():
    """Return the configured channel, falling back to the default."""
    return os.environ.get("PULSE_CHANNEL", DEFAULT_CHANNEL)
