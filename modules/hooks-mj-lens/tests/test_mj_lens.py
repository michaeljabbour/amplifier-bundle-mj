"""Tests for hooks-mj-lens — isolated, no real coordinator/session/LLM."""

import pytest

from amplifier_module_hooks_mj_lens import mount


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

    assert result is not None and result["name"] == "hooks-mj-lens"
    assert len(coordinator.hooks.registered) == 1
    reg = coordinator.hooks.registered[0]
    assert reg["event"] == "session:start"
    assert reg["name"] == "hooks-mj-lens"
    assert callable(reg["handler"])


@pytest.mark.asyncio
async def test_handler_injects_mj_lens_context():
    coordinator = MockCoordinator()
    await mount(coordinator, {})
    handler = coordinator.hooks.registered[0]["handler"]

    res = await handler("session:start", {})
    assert res.action == "inject_context"
    assert res.context_injection_role == "system"
    assert res.ephemeral is False
    # The injected instruction carries MJ's lens, in his register.
    assert "MJ Lens" in res.context_injection
    assert "grit" in res.context_injection.lower()
    assert "buildable" in res.context_injection.lower()
    # The disciplined-subtraction move — the bundle's mission — is part of the lens.
    assert "subtraction" in res.context_injection.lower()
    assert "deletion" in res.context_injection.lower()


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
