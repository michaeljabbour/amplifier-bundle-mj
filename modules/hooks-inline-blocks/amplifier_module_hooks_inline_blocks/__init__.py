"""hooks-inline-blocks — surface the insight / machete / MJ-lens inline blocks.

Consolidates the three formerly-separate `hooks-insight-blocks`, `hooks-machete-blocks`,
and `hooks-mj-lens` modules into ONE parametrized brick. This is a *bug fix*, not just a
refactor: the three predecessor modules registered on `session:start`, but the kernel's
session-lifecycle emission path (`amplifier_core/session.py`, the Rust `session.rs`
`execute()` path) fires that event and never captures or applies the returned
`HookResult` — no `coordinator.process_hook_result()` call, no `context.add_message()`.
Confirmed at the kernel-source level by three independent experts (core, foundation,
amplifier). The three predecessor hooks were silent no-ops: they mounted, registered,
fired once — and the kernel threw their `inject_context` result on the floor.

The fix: register on `prompt:submit` (config-driven, default `prompt:submit`) instead.
That event IS routed through `process_hook_result()` / `context.add_message()` by the
proven `hooks-explanatory` pattern (core `hook_dispatch.rs`), so the injected system
instruction actually reaches the model. Because `prompt:submit` fires on every user turn
(not once per session, unlike `session:start`), a per-(session_id, block-name) `_fired`
guard reproduces the original "inject exactly once per session" semantics.

Why ONE module instead of three: `amplifier_foundation/dicts/merge.py`'s
`merge_module_lists()` indexes bundle module entries by `config.get("id") or
config.get("module")` and deep-merges collisions on that key during composition. Three
behavior entries all keyed `module: hooks-inline-blocks` would collapse to one during
composition rather than yielding three independent registrations. The robust, contract-
safe shape is a single module entry that accepts a `blocks: [...]` list and registers one
handler per block — one brick, one mount, N handlers — which is well within the
`HookRegistry.register()` contract (multiple handlers on the same event, distinct
`name`/`priority`; see core `HOOKS_API.md` §Registration).

Each block keeps its original per-variant hook name (`hooks-insight-blocks`,
`hooks-machete-blocks`, `hooks-mj-lens`) for `coordinator.hooks.register(name=...)`.
The instruction text was inherited byte-for-byte at consolidation time but has since
been rewritten in place — see the constants below. Markdown blockquotes /
backtick-fenced blocks remain the display convention: the model's own text IS the block,
there is no special renderer. Fail-open throughout: any error in a single block's
injection degrades that block to a no-op rather than breaking the session, and does not
affect the other blocks.

`mount()` returns a cleanup callable that unregisters every handler it registered,
correcting the predecessor modules' contract gap (they returned a plain metadata dict,
with nothing for the kernel to invoke at teardown).
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from amplifier_core import HookResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Instruction constants — the text each block teaches the model to emit.
#
# Originally inherited byte-for-byte from three predecessor modules
# (hooks-insight-blocks, hooks-machete-blocks, hooks-mj-lens); rewritten in place
# since, so they no longer match those sources.
#
# WHY BLOCKQUOTES (★, ✂): the amplifier CLI renders assistant text through Rich
# and strips raw ANSI, so a blockquote is the only way to get a COLORED left
# gutter — Rich auto-draws a magenta "▌" edge, and everything after the "> "
# inherits it. Magenta is the only colored-gutter option the renderer exposes.
# The MJ Lens (🔪) uses backtick-fenced U+2500 rules instead, which read as plain
# grey; it is the directional verdict, so it is deliberately not a magenta accent.
# The three markers keep the blocks distinct from each other.
#
# The model does not need any of the above — it is renderer rationale for the
# maintainer, so it lives here and NOT in the injected prompt text.
#
# LENGTH IS THE POINT. These are injected into every session, every turn. They
# were cut from a combined 1,084 words to 592 precisely because always-on
# verbosity crowds the session and leaks the bundle's insider vocabulary into
# user-facing output. Adding a rule here costs every turn of every session;
# prefer cutting one.
#
# The budget is ENFORCED, not just documented: tests/test_inline_blocks.py has a
# per-block word ceiling. Growing a block fails the suite until you raise the
# ceiling deliberately. Do not paste live word counts into this comment — they
# rot silently (they already did once). The test holds the numbers.
#
# NO FIXED-SLOT TEMPLATES. The MJ Lens block used to mandate six bullet headings
# (**Bricks**, **Grit**, **Subtraction**, ...). Six slots meant six slots got
# filled every time, whether or not there was anything to say — which set a
# length floor AND put the insider labels straight into user-facing output.
# Specify the reasoning MOVE, not the headings.
# ---------------------------------------------------------------------------
INSIGHT_BLOCK_INSTRUCTIONS = """\
# ★ Insight callouts

When the work just taught something, say so — briefly — as a blockquote leading
with `★ **Insight:**`, `> ` on every line:

> ★ **Insight:** the retry wrapper was safe to delete because the caller already
> retries — the inner loop was belt-and-suspenders. Principle: one owner per concern.

Three moves: what happened, why it holds *here* — name the one or two concrete
details from their actual code that make it true — then the rule they can carry
elsewhere. Skip the middle move and it's a slogan. Skip the last and it's a
status update.

Plain words; translate any unavoidable term in the same breath. Two sentences,
then stop. No throat-clearing, no flattery.

It teaches; it doesn't act, recommend, or judge — ordinary offers (commit this,
run the tests) stay in your own plain voice. Nothing worth teaching → no block.
Most turns get none. An insight you raise for everything stops being one.
"""

MACHETE_BLOCK_INSTRUCTIONS = """\
# ✂ Machete callouts

When there's real fat and the next move is a cut, offer it — as a blockquote
leading with `✂ **MJ:**`, `> ` on every line:

> ✂ **MJ:** `legacy_export/` is 400 lines behind a flag that's been off since
> March — drop into `/machete` and I'll cut it subtraction-first, tests green,
> nothing removed I can't prove is safe.

Point at the actual fat: name the file, the function, the dead path — one or two
specifics from what they're building. A vague offer gets ignored.

Match how they talk: terse for engineers, plain and benefit-led for everyone
else, one breath when they're in a hurry. One sentence, attributed to MJ.

It offers; it doesn't cut, teach, or judge — ordinary offers (commit this, open a
PR) stay in your own plain voice. No fat you can point at → no block. Most turns
get none. A recommendation you raise for everything stops being one.
"""

MJ_LENS_INSTRUCTIONS = """\
# 🔪 MJ Lens

For reviews, decisions, and design calls — not lookups or plain execution.
Between two rule lines (U+2500), like this:

`🔪 MJ Lens ─────────────────────────────────`
Ship single-tenant first. Multi-tenancy here is three separate subsystems — auth
scoping, per-tenant migrations, and stopping one customer's load from starving
another — and you have one customer. Best case for building it now: adding it
later is expensive. But you don't yet know which of the three you'll actually
need, so you'd be paying for all three to avoid guessing at one. Smallest move:
put the tenant ID in the schema now, defer the other two.
`─────────────────────────────────────────────`

Say the call, then show the work — the strongest argument against it, and what
you'd remove. Ground it in one or two specifics from what they're actually
building: the file, the call path, the constraint that decides it. Close with the
smallest reversible next step, or — when the call is genuinely theirs — the one
question they should answer first.

Six things to have thought about, none of them headings to fill: what the
first-principle pieces are; whether the reasoning is forced, evidenced, or merely
plausible; the strongest case against; how heavy a change this really needs
(rework the shape, a contained refinement, or polish); what survives deletion;
what's buildable now. Think all six. Say only what earned the space.

Warm but curt. Short declaratives, plain words, no hedging. Four or five
sentences. It sets direction; it doesn't cut — when the answer is "rework it,"
hand the cutting to the occams-machete blade. A lens you raise for everything
stops being a lens.
"""

# ---------------------------------------------------------------------------
# Block registry and resolution
# ---------------------------------------------------------------------------

# Maps a `blocks[].use` key to (hook-name, instructions). Hook names match the
# predecessor modules' `coordinator.hooks.register(name=...)` values exactly, so
# any tooling/logging keyed on those names keeps working unchanged.
_DEFAULT_BLOCKS: dict[str, tuple[str, str]] = {
    "insight": ("hooks-insight-blocks", INSIGHT_BLOCK_INSTRUCTIONS),
    "machete": ("hooks-machete-blocks", MACHETE_BLOCK_INSTRUCTIONS),
    "mj-lens": ("hooks-mj-lens", MJ_LENS_INSTRUCTIONS),
}

# Per-(session_id, hook-name) fire-once guard. `prompt:submit` fires on every user
# turn (unlike the discarded `session:start`), so this guard reproduces the
# predecessor modules' "inject exactly once per session" semantics: once a block
# has fired for a session, later turns in that same session return `continue`
# instead of re-injecting the instructions. Module-level (not per-mount) so it
# survives across any re-mount within the same process; tests clear it explicitly
# between cases (see tests/test_inline_blocks.py).
_fired: set[tuple[Any, str]] = set()


def _resolve_blocks(
    config: dict[str, Any],
) -> list[tuple[str, str, dict[str, Any]]]:
    """Resolve the configured `blocks` list against `_DEFAULT_BLOCKS`.

    Returns a list of (hook_name, base_instructions, block_config) tuples for every
    enabled, recognized block, in configuration order. Unrecognized `use` keys are
    skipped with a warning — fail-open, not a raised exception — so a typo in one
    block's config never prevents the other blocks from mounting. If `blocks` is
    omitted entirely, all three default blocks are used (insight, machete, mj-lens).
    """
    raw_blocks = config.get("blocks")
    if not raw_blocks:
        raw_blocks = [{"use": key} for key in _DEFAULT_BLOCKS]

    resolved: list[tuple[str, str, dict[str, Any]]] = []
    for block_config in raw_blocks:
        use = block_config.get("use")
        entry = _DEFAULT_BLOCKS.get(use)
        if entry is None:
            logger.warning(
                "hooks-inline-blocks: unknown block 'use: %s'; skipping", use
            )
            continue
        if not block_config.get("enabled", True):
            continue
        hook_name, base_instructions = entry
        resolved.append((hook_name, base_instructions, block_config))
    return resolved


def _build_instructions(base_instructions: str, block_config: dict[str, Any]) -> str:
    """Assemble the injection string for a single block. Isolated so failures here
    stay contained, matching the predecessor modules' per-module convention."""
    extra = block_config.get("extra_instructions")
    if isinstance(extra, str) and extra.strip():
        return base_instructions + "\n" + extra.strip() + "\n"
    return base_instructions


def _make_handler(
    hook_name: str,
    base_instructions: str,
    block_config: dict[str, Any],
    session_id: Any,
    ephemeral: bool,
) -> Callable[[str, dict[str, Any]], Awaitable[HookResult]]:
    """Build a fire-once, fail-open handler for a single block."""

    async def handler(event: str, data: dict[str, Any]) -> HookResult:
        key = (session_id, hook_name)
        if key in _fired:
            return HookResult(action="continue")
        _fired.add(key)
        try:
            instructions = _build_instructions(base_instructions, block_config)
            return HookResult(
                action="inject_context",
                context_injection=instructions,
                context_injection_role="system",
                ephemeral=ephemeral,
            )
        except Exception:  # fail-open: never break a session over a briefing
            logger.exception(
                "hooks-inline-blocks: injection failed for block '%s'; "
                "degrading to no-op",
                hook_name,
            )
            return HookResult(action="continue")

    return handler


async def mount(
    coordinator: Any, config: dict[str, Any] | None = None
) -> Callable[[], Awaitable[None]] | None:
    """Register one fire-once handler per configured block.

    Honors `enabled` (default True, whole-module kill switch), `event` (default
    "prompt:submit" — the event the kernel actually routes `inject_context`
    results through; `session:start` is discarded, see module docstring),
    `ephemeral` (default False — persist the injection in conversation history,
    matching the predecessor modules), `priority` (default 50), and `blocks`
    (default: all three — insight, machete, mj-lens). Each block entry may set its
    own `use`, `enabled`, and `extra_instructions`.

    Returns a cleanup callable that unregisters every handler this call
    registered, correcting the predecessor modules' contract gap (they returned a
    metadata dict with nothing for the kernel to invoke at teardown). Returns
    `None` when the module is disabled or no blocks resolve — both are valid
    "nothing to clean up" states per the mount() contract.
    """
    config = config or {}

    if not config.get("enabled", True):
        logger.info("hooks-inline-blocks disabled via config")
        return None

    event = config.get("event", "prompt:submit")
    ephemeral = bool(config.get("ephemeral", False))
    priority = int(config.get("priority", 50))
    session_id = getattr(coordinator, "session_id", None)

    blocks = _resolve_blocks(config)
    if not blocks:
        logger.info("hooks-inline-blocks: no blocks resolved; nothing to mount")
        return None

    unregisters: list[Callable[[], Any]] = []
    for hook_name, base_instructions, block_config in blocks:
        handler = _make_handler(
            hook_name, base_instructions, block_config, session_id, ephemeral
        )
        unregister = coordinator.hooks.register(
            event=event,
            handler=handler,
            priority=priority,
            name=hook_name,
        )
        unregisters.append(unregister)

    async def cleanup() -> None:
        for unregister in unregisters:
            try:
                unregister()
            except Exception:
                logger.exception(
                    "hooks-inline-blocks: cleanup failed to unregister a handler"
                )

    logger.info(
        "hooks-inline-blocks mounted: %d block(s) will surface inline on '%s'",
        len(unregisters),
        event,
    )
    return cleanup
