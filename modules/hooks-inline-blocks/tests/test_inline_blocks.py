"""Tests for the consolidated hooks-inline-blocks module.

Covers the mechanism fix at the heart of this consolidation: registration on the
config-driven event (default `prompt:submit`, NOT the kernel-discarded
`session:start`), config-driven `ephemeral`, the per-(session_id, block-name)
fire-once guard, per-block enable/disable and unknown-`use` handling, the
cleanup callable returned by `mount()`, and fail-open behavior on exception.

Also enforces the ALWAYS-ON WORD BUDGET (test 12). These three constants are
injected into every session on every turn, so their size is a real cost, not a
style preference. The budget used to live in a code comment and silently rotted
within a single changeset. It lives here now, because comments don't run.
"""

from __future__ import annotations

import pathlib
import re
from typing import Any

import pytest

from amplifier_module_hooks_inline_blocks import (
    INSIGHT_BLOCK_INSTRUCTIONS,
    MACHETE_BLOCK_INSTRUCTIONS,
    MJ_LENS_INSTRUCTIONS,
    _fired,
    mount,
)


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


# ---------------------------------------------------------------------------
# 12. Always-on word budget. These three constants are injected into EVERY
#     session on EVERY turn, so their size is a running cost paid by every
#     user, forever. A previous version of this budget lived in a code comment
#     and went stale inside a single changeset — two exemplar fixes added 36
#     words and nothing objected. Comments don't run; this does.
#
#     If you are here because this test failed: that is the test working. You
#     added words to an always-on prompt. Either cut something else out, or
#     raise the ceiling deliberately and say why in the commit message.
# ---------------------------------------------------------------------------
WORD_CEILINGS = {
    "INSIGHT_BLOCK_INSTRUCTIONS": 165,
    "MACHETE_BLOCK_INSTRUCTIONS": 165,
    "MJ_LENS_INSTRUCTIONS": 275,
}
TOTAL_CEILING = 600  # was 1084 before the 2026-08 voice pass


@pytest.mark.parametrize("name,ceiling", sorted(WORD_CEILINGS.items()))
def test_block_stays_within_word_budget(name: str, ceiling: int):
    text = {
        "INSIGHT_BLOCK_INSTRUCTIONS": INSIGHT_BLOCK_INSTRUCTIONS,
        "MACHETE_BLOCK_INSTRUCTIONS": MACHETE_BLOCK_INSTRUCTIONS,
        "MJ_LENS_INSTRUCTIONS": MJ_LENS_INSTRUCTIONS,
    }[name]
    actual = len(text.split())
    assert actual <= ceiling, (
        f"{name} is {actual} words, over its {ceiling}-word always-on ceiling. "
        f"This text is injected every turn of every session. Cut something, or "
        f"raise the ceiling on purpose."
    )


def test_total_always_on_budget():
    total = sum(
        len(t.split())
        for t in (
            INSIGHT_BLOCK_INSTRUCTIONS,
            MACHETE_BLOCK_INSTRUCTIONS,
            MJ_LENS_INSTRUCTIONS,
        )
    )
    assert total <= TOTAL_CEILING, (
        f"Combined always-on instructions are {total} words, over the "
        f"{TOTAL_CEILING}-word ceiling."
    )


# ---------------------------------------------------------------------------
# 13. No fixed-slot templates. The MJ Lens block used to mandate six bullet
#     headings (**Bricks**, **Grit**, **Subtraction**, ...). Six slots meant six
#     slots got filled every time whether or not there was anything to say,
#     which set a length floor AND pushed the bundle's insider vocabulary
#     straight into user-facing output. Specify the reasoning MOVE, not the
#     headings. This guards against the template growing back.
# ---------------------------------------------------------------------------
RETIRED_SLOT_LABELS = [
    "**Bricks**",
    "**Grit**",
    "**Subtraction**",
    "**Buildable now**",
    "**Adversarial / circular**",
    "**How solid is it?**",
    # Removed 2026-08-12 from the mj-reviewer "Grit & verdict" section. The
    # sandpaper scale is calibration, not wording — printing it as a label is
    # the same regression in a different costume. Extend this list in the SAME
    # commit that removes a label, or the guard silently protects history
    # instead of the present.
    "**Coarse**",
    "**Medium**",
    "**Fine**",
]


@pytest.mark.parametrize("label", RETIRED_SLOT_LABELS)
def test_mj_lens_has_no_fixed_slot_headings(label: str):
    assert label not in MJ_LENS_INSTRUCTIONS, (
        f"{label} is back in the MJ Lens block as a bold heading. That is the "
        f"six-slot template this pass removed: required headings get filled "
        f"whether or not they have content. Keep the six as things to have "
        f"thought about, not labels to print."
    )


# ---------------------------------------------------------------------------
# 14. The no-slot rule also covers the two MARKDOWN surfaces that reach a model.
#     `agents/mj-reviewer.md` produces delegated output, and
#     `context/mj-profile.md` is @mentioned into that same agent's context — so
#     a bold label reintroduced in either one regrows the template just as
#     effectively as one in the hook block above. Test 13 guarded only the
#     lowest-blast-radius surface; this guards the other two.
#
#     Skips cleanly when the module is installed standalone (no repo tree).
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
GUARDED_MARKDOWN = [
    "agents/mj-reviewer.md",
    "context/mj-profile.md",
]


@pytest.mark.parametrize("rel_path", GUARDED_MARKDOWN)
def test_markdown_surfaces_have_no_fixed_slot_headings(rel_path: str):
    path = _REPO_ROOT / rel_path
    if not path.is_file():
        pytest.skip(f"{rel_path} not present (module installed standalone)")
    text = path.read_text(encoding="utf-8")
    offenders = [label for label in RETIRED_SLOT_LABELS if label in text]
    assert not offenders, (
        f"{rel_path} reintroduces retired slot label(s) {offenders} as bold "
        f"headings. These are reasoning moves, not labels to print — bolding "
        f"them is how the six-slot template grows back, and this file reaches "
        f"the model. Write them as plain sentences."
    )


# ---------------------------------------------------------------------------
# 15. Principle parity between the mj-reviewer AGENT and the mj-lens SKILL.
#
#     MJ's review judgment is stated twice on purpose: the agent runs in a
#     FORKED sub-session (can't see the current conversation), the skill loads
#     INLINE (can). Two consumers, two contexts, one body of judgment.
#
#     The cost of that duplication is drift, and it is not hypothetical — the
#     principle set has already changed once (commit 2ef7608 added P10). There
#     is no @mention expansion in skill bodies, so the two files genuinely
#     cannot share a single source today. This test is the cheap substitute:
#     add or remove a principle in one file and the suite goes red until the
#     other follows.
#
#     Skips cleanly when the module is installed standalone (no repo tree).
# ---------------------------------------------------------------------------
_AGENT_PRINCIPLES = _REPO_ROOT / "agents" / "mj-reviewer.md"
_SKILL_PRINCIPLES = _REPO_ROOT / "skills" / "mj-lens" / "SKILL.md"


def test_agent_and_skill_state_the_same_number_of_principles():
    if not (_AGENT_PRINCIPLES.is_file() and _SKILL_PRINCIPLES.is_file()):
        pytest.skip("repo tree not present (module installed standalone)")

    agent = _AGENT_PRINCIPLES.read_text(encoding="utf-8")
    skill = _SKILL_PRINCIPLES.read_text(encoding="utf-8")

    # Agent states them as bold **P1 — ...** headings.
    agent_ids = set(re.findall(r"\*\*(P\d+)\s*—", agent))
    # Skill states them as a numbered list under "The judgment behind it".
    skill_body = skill.split("## The judgment behind it", 1)
    assert len(skill_body) == 2, (
        "skills/mj-lens/SKILL.md no longer has a '## The judgment behind it' "
        "section — if the principles moved, update this test with them."
    )
    skill_nums = set(re.findall(r"^(\d+)\.\s+\*\*", skill_body[1], re.MULTILINE))

    assert len(agent_ids) == len(skill_nums), (
        f"Principle drift: agents/mj-reviewer.md states {len(agent_ids)} "
        f"principles {sorted(agent_ids)}, skills/mj-lens/SKILL.md states "
        f"{len(skill_nums)}. These are two renderings of one body of judgment "
        f"(forked agent vs inline skill). Add or remove in both, or this "
        f"bundle ships two versions of MJ that disagree."
    )


# ---------------------------------------------------------------------------
# 16. Every agent the behavior wires must exist on disk, and every agent on disk
#     must be wired. A bundle that advertises a lens it cannot mount fails
#     silently -- delegate() just errors at call time, long after review.
#
#     This caught nothing when written; it exists because the bench grew from
#     three agents to four and the wiring is a second place to forget.
# ---------------------------------------------------------------------------
def test_behavior_agent_wiring_matches_agents_on_disk():
    behavior = _REPO_ROOT / "behaviors" / "mj.yaml"
    agents_dir = _REPO_ROOT / "agents"
    if not (behavior.is_file() and agents_dir.is_dir()):
        pytest.skip("repo tree not present (module installed standalone)")

    # Parsed with regex, not yaml: this module ships with no yaml dependency
    # (dev extras are pytest + pytest-asyncio only), and adding one so a test can
    # read a sibling file would be the tail wagging the dog.
    btext = behavior.read_text(encoding="utf-8")
    agents_block = btext.split("\nagents:", 1)
    assert len(agents_block) == 2, "behaviors/mj.yaml has no top-level `agents:` block"
    block = agents_block[1].split("\ncontext:", 1)[0]
    wired_names = set(re.findall(r"^\s*-\s*mj:(\S+)\s*$", block, re.MULTILINE))

    on_disk = set()
    for f in sorted(agents_dir.glob("*.md")):
        fm = f.read_text(encoding="utf-8").split("---", 2)[1]
        m = re.search(r"^\s{2}name:\s*(\S+)\s*$", fm, re.MULTILINE)
        assert m, f"{f.name} frontmatter has no `  name:` under meta:"
        on_disk.add(m.group(1))

    assert wired_names == on_disk, (
        f"Agent wiring drift.\n"
        f"  wired in behaviors/mj.yaml : {sorted(wired_names)}\n"
        f"  present in agents/         : {sorted(on_disk)}\n"
        f"  wired but missing on disk  : {sorted(wired_names - on_disk)}\n"
        f"  on disk but never wired    : {sorted(on_disk - wired_names)}\n"
        f"An agent that is present but unwired can never be delegated to; one "
        f"that is wired but absent fails at call time, not at load."
    )
