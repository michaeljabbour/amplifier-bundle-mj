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
_anthropic_fable_client = None
_openai_client = None


def _get_anthropic(model: str = ""):
    """Return the Anthropic client. claude-fable-* models require the
    data-retention endpoint key (ANTHROPIC_FABLE_API_KEY); others use
    ANTHROPIC_API_KEY."""
    global _anthropic_client, _anthropic_fable_client
    import anthropic  # imported here so module import never needs the SDK

    if model.startswith("claude-fable"):
        if _anthropic_fable_client is None:
            key = os.environ.get("ANTHROPIC_FABLE_API_KEY")
            if not key:
                raise RuntimeError("ANTHROPIC_FABLE_API_KEY is not set (required for claude-fable-* models).")
            _anthropic_fable_client = anthropic.Anthropic(api_key=key)
        return _anthropic_fable_client
    if _anthropic_client is None:
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
        client = _get_anthropic(model)
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if not model.startswith("claude-fable"):
            kwargs["temperature"] = temperature  # fable models reject temperature (deprecated)
        resp = client.messages.create(**kwargs)
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
        kwargs: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if model.startswith("gpt-5"):
            # gpt-5.x rejects max_tokens and fixed temperature; reasoning tokens
            # count against the completion budget, so give generous headroom.
            kwargs["max_completion_tokens"] = max(max_tokens * 4, 2000)
        else:
            kwargs["temperature"] = temperature
            kwargs["max_tokens"] = max_tokens
        resp = client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content
        return (content or "").strip()

    return _with_retry(_do, f"openai:{model}")
