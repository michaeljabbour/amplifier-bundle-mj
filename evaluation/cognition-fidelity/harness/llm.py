"""Thin, resilient wrappers around the Anthropic and OpenAI SDKs.

Each call retries with exponential backoff + jitter on rate-limit and transient
errors. Clients are constructed lazily and memoized so importing this module
never requires API keys (the syntax/import checks pass without secrets).
"""

from __future__ import annotations

import os
import random
import time

from config import (
    BACKOFF_BASE_SECONDS,
    BACKOFF_MAX_SECONDS,
    MAX_RETRIES,
)

# ---------------------------------------------------------------------------
# Lazy singleton clients
# ---------------------------------------------------------------------------
_anthropic_client = None
_openai_client = None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic  # imported here so module import never needs the SDK

        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in the environment.")
        _anthropic_client = anthropic.Anthropic(api_key=key)
    return _anthropic_client


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set in the environment.")
        _openai_client = OpenAI(api_key=key)
    return _openai_client


def _is_retryable(exc: Exception) -> bool:
    """Heuristic: retry on rate limits, timeouts, connection blips, and 5xx."""
    name = type(exc).__name__.lower()
    if any(
        tok in name
        for tok in (
            "ratelimit",
            "timeout",
            "connection",
            "apistatus",
            "internalserver",
            "serviceunavailable",
            "overloaded",
        )
    ):
        return True
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if isinstance(status, int) and (status == 429 or 500 <= status < 600):
        return True
    return False


def _with_retry(fn, what: str):
    """Run fn() with exponential backoff. Raises the last error if all fail."""
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — we classify then re-raise
            last_exc = exc
            if not _is_retryable(exc) or attempt == MAX_RETRIES - 1:
                raise
            delay = min(BACKOFF_BASE_SECONDS * (2**attempt), BACKOFF_MAX_SECONDS)
            delay += random.uniform(0, delay * 0.25)  # jitter
            time.sleep(delay)
    # Unreachable, but keeps type-checkers happy.
    raise last_exc if last_exc else RuntimeError(f"{what} failed without exception")


def call_anthropic(
    *,
    model: str,
    system: str,
    user: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Single-turn Anthropic completion. Returns the concatenated text blocks."""

    def _do() -> str:
        client = _get_anthropic()
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = [
            getattr(block, "text", "")
            for block in resp.content
            if getattr(block, "type", None) == "text"
        ]
        return "\n".join(p for p in parts if p).strip()

    return _with_retry(_do, f"anthropic:{model}")


def call_openai(
    *,
    model: str,
    system: str,
    user: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Single-turn OpenAI chat completion. Returns the message content."""

    def _do() -> str:
        client = _get_openai()
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = resp.choices[0].message.content
        return (content or "").strip()

    return _with_retry(_do, f"openai:{model}")
