"""Tests for the consolidated hooks-inline-blocks module.

Covers the mechanism fix at the heart of this consolidation: registration on the
config-driven event (default `prompt:submit`, NOT the kernel-discarded
`session:start`), config-driven `ephemeral`, the per-(session_id, block-name)
fire-once guard, per-block enable/disable and unknown-`use` handling, the
cleanup callable returned by `mount()`, and fail-open behavior on exception.
"""

from __future__ import annotations

from typing import Any

import pytest

from amplifier_module_hooks_inline_blocks import _fired, mount


class MockHookRegistry:
    """Records registrations; `register()` returns an unregister callable, as the
    real amplifier-core HookRegistry does."""

    def __init__(self) -> None:
        self.registrations: list[dict[str, Any]] = []
        self.unregistered: list[str] = []

    def register(self, *, event: str, handler, priority: int, name: str):
        entry = {
            "event": event,
            "handler": handler,
            "priority": priority,
            "name": name,
        }
        self.registrations.append(entry)

        def unregister() -> None:
            self.unregistered.append(name)

        return unregister


class MockCoordinator:
    """Minimal coordinator stand-in. Exposes `session_id` (mount() reads it via
    getattr) and a `.hooks` registry."""

    def __init__(self, session_id: str = "session-1") -> None:
        self.session_id = session_id
        self.hooks = MockHookRegistry()


@pytest.fixture(autouse=True)
def _clear_fired_state():
    """The fire-once guard is module-level global state (by design — it must
    survive across multiple `prompt:submit` events within one real session).
    Tests must not leak state into each other, so clear it before and after
    every test."""
    _fired.clear()
    yield
    _fired.clear()


async def _fire(coordinator: MockCoordinator, hook_name: str, event: str = "prompt:submit"):
    """Find the registered handler by name and invoke it once."""
    for entry in coordinator.hooks.registrations:
        if entry["name"] == hook_name:
            return await entry["handler"](event, {})
    raise AssertionError(f"no handler registered with name={hook_name!r}")


# ---------------------------------------------------------------------------
# 1. Default mount registers all three blocks under their original hook names.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mount_registers_default_three_blocks_with_expected_names():
    coordinator = MockCoordinator()
    cleanup = await mount(coordinator, config=None)

    names = {entry["name"] for entry in coordinator.hooks.registrations}
    assert names == {"hooks-insight-blocks", "hooks-machete-blocks", "hooks-mj-lens"}
    assert cleanup is not None


# ---------------------------------------------------------------------------
# 2. Default event is prompt:submit — the event the kernel actually routes
#    inject_context through (session:start is discarded, see module docstring).
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mount_default_event_is_prompt_submit():
    coordinator = MockCoordinator()
    await mount(coordinator, config=None)

    events = {entry["event"] for entry in coordinator.hooks.registrations}
    assert events == {"prompt:submit"}


# ---------------------------------------------------------------------------
# 3. Event is config-driven — can be overridden (e.g. back to provider:request
#    as a documented fallback path).
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mount_custom_event_config_respected():
    coordinator = MockCoordinator()
    await mount(coordinator, config={"event": "provider:request"})

    events = {entry["event"] for entry in coordinator.hooks.registrations}
    assert events == {"provider:request"}


# ---------------------------------------------------------------------------
# 4. Default ephemeral is False — the injection persists in conversation
#    history, matching the predecessor modules' behavior.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mount_default_ephemeral_false():
    coordinator = MockCoordinator()
    await mount(coordinator, config=None)

    result = await _fire(coordinator, "hooks-insight-blocks")
    assert result.action == "inject_context"
    assert result.ephemeral is False


# ---------------------------------------------------------------------------
# 5. ephemeral is config-driven — can be flipped to True.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mount_ephemeral_true_config_respected():
    coordinator = MockCoordinator()
    await mount(coordinator, config={"ephemeral": True})

    result = await _fire(coordinator, "hooks-machete-blocks")
    assert result.action == "inject_context"
    assert result.ephemeral is True


# ---------------------------------------------------------------------------
# 6. mount() returns a cleanup callable that unregisters every handler —
#    correcting the predecessor modules' contract gap.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cleanup_callable_unregisters_all_handlers():
    coordinator = MockCoordinator()
    cleanup = await mount(coordinator, config=None)
    assert cleanup is not None

    await cleanup()

    assert set(coordinator.hooks.unregistered) == {
        "hooks-insight-blocks",
        "hooks-machete-blocks",
        "hooks-mj-lens",
    }


# ---------------------------------------------------------------------------
# 7. Fire-once guard: a block fires exactly once per (session_id, name); a
#    second prompt:submit in the SAME session returns "continue" instead of
#    re-injecting.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_handler_fires_once_per_session_then_continues():
    coordinator = MockCoordinator(session_id="session-A")
    await mount(coordinator, config=None)

    first = await _fire(coordinator, "hooks-mj-lens")
    second = await _fire(coordinator, "hooks-mj-lens")

    assert first.action == "inject_context"
    assert second.action == "continue"


# ---------------------------------------------------------------------------
# 8. Whole-module disable (`enabled: false`) returns None and registers
#    nothing.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_module_disabled_returns_none_and_registers_nothing():
    coordinator = MockCoordinator()
    cleanup = await mount(coordinator, config={"enabled": False})

    assert cleanup is None
    assert coordinator.hooks.registrations == []


# ---------------------------------------------------------------------------
# 9. Per-block disable skips only that block; the others still mount.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_per_block_disabled_skips_only_that_block():
    coordinator = MockCoordinator()
    await mount(
        coordinator,
        config={
            "blocks": [
                {"use": "insight", "enabled": False},
                {"use": "machete"},
                {"use": "mj-lens"},
            ]
        },
    )

    names = {entry["name"] for entry in coordinator.hooks.registrations}
    assert names == {"hooks-machete-blocks", "hooks-mj-lens"}


# ---------------------------------------------------------------------------
# 10. An unrecognized `use` value is skipped (fail-open), never raises, and
#     does not prevent other valid blocks from mounting.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unknown_block_use_skipped_without_raising():
    coordinator = MockCoordinator()
    cleanup = await mount(
        coordinator,
        config={"blocks": [{"use": "does-not-exist"}, {"use": "insight"}]},
    )

    names = {entry["name"] for entry in coordinator.hooks.registrations}
    assert names == {"hooks-insight-blocks"}
    assert cleanup is not None


# ---------------------------------------------------------------------------
# 11. Fail-open: an exception raised while building instructions degrades the
#     handler to "continue" rather than propagating.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_handler_fail_open_returns_continue_on_exception(monkeypatch):
    import amplifier_module_hooks_inline_blocks as module

    def _boom(*_args, **_kwargs):
        raise RuntimeError("synthetic failure for fail-open test")

    monkeypatch.setattr(module, "_build_instructions", _boom)

    coordinator = MockCoordinator()
    await mount(coordinator, config=None)

    result = await _fire(coordinator, "hooks-insight-blocks")
    assert result.action == "continue"
