"""Tests for hooks-machete-blocks — isolated, no real coordinator/session/LLM."""

import pytest

from amplifier_module_hooks_machete_blocks import mount


class MockHookRegistry:
    def __init__(self):
        self.registered = []

    def register(self, event, handler, priority=0, name=None):
        self.registered.append(
            {"event": event, "handler": handler, "priority": priority, "name": name}
        )


class MockCoordinator:
    def __init__(self):
        self.hooks = MockHookRegistry()


@pytest.mark.asyncio
async def test_mount_registers_session_start_handler():
    coordinator = MockCoordinator()
    result = await mount(coordinator, {})

    assert result is not None and result["name"] == "hooks-machete-blocks"
    assert len(coordinator.hooks.registered) == 1
    reg = coordinator.hooks.registered[0]
    assert reg["event"] == "session:start"
    assert reg["name"] == "hooks-machete-blocks"
    assert callable(reg["handler"])


@pytest.mark.asyncio
async def test_handler_injects_machete_block_context():
    coordinator = MockCoordinator()
    await mount(coordinator, {})
    handler = coordinator.hooks.registered[0]["handler"]

    res = await handler("session:start", {})
    assert res.action == "inject_context"
    assert res.context_injection_role == "system"
    assert res.ephemeral is False
    # The injected instruction carries the Machete callout block format.
    assert "Machete" in res.context_injection
    assert "/machete" in res.context_injection
    assert "callout" in res.context_injection.lower()
    # The scissors marker keeps it separable from the MJ Lens (🔪) review block.
    assert "✂" in res.context_injection
    # A Markdown blockquote is the renderer-native colored gutter (Rich paints
    # markdown.block_quote magenta); it is NOT a hand-drawn bar or dramatic rule.
    assert "blockquote" in res.context_injection.lower()
    # Exact shape: scissors gutter marker + bold "MJ:" label inside a blockquote.
    assert "> ✂ **MJ:**" in res.context_injection
    assert "───" not in res.context_injection
    # Scope guard: this AUGMENTS Amplifier (recommends /machete only); it must not
    # reskin Amplifier's ordinary offers (commit, PR, tests) in this block.
    assert "augment" in res.context_injection.lower()


@pytest.mark.asyncio
async def test_extra_instructions_are_appended():
    coordinator = MockCoordinator()
    await mount(coordinator, {"extra_instructions": "SENTINEL-EXTRA"})
    handler = coordinator.hooks.registered[0]["handler"]

    res = await handler("session:start", {})
    assert "SENTINEL-EXTRA" in res.context_injection


@pytest.mark.asyncio
async def test_disabled_registers_nothing():
    coordinator = MockCoordinator()
    result = await mount(coordinator, {"enabled": False})

    assert result["enabled"] is False
    assert coordinator.hooks.registered == []


@pytest.mark.asyncio
async def test_priority_is_passed_through():
    coordinator = MockCoordinator()
    await mount(coordinator, {"priority": 25})
    assert coordinator.hooks.registered[0]["priority"] == 25
