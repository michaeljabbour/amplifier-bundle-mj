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
`hooks-machete-blocks`, `hooks-mj-lens`) for `coordinator.hooks.register(name=...)`, and
its instruction text is copied byte-for-byte from the predecessor module it replaces —
this is a mechanism fix, not a rewrite of the injected content. Markdown blockquotes /
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
# Instruction constants — copied byte-for-byte from the predecessor modules:
#   INSIGHT_BLOCK_INSTRUCTIONS  <- hooks-insight-blocks/.../__init__.py:37-74
#   MACHETE_BLOCK_INSTRUCTIONS  <- hooks-machete-blocks/.../__init__.py:30-64
#   MJ_LENS_INSTRUCTIONS       <- hooks-mj-lens/.../__init__.py:20-51
# Only the surrounding mount/registration mechanism changed; the text the model is
# taught to emit did not.
# ---------------------------------------------------------------------------

# The inline block the model is asked to emit. It is a Markdown blockquote, NOT a
# hand-drawn `★ Insight ─────` bar: the amplifier CLI renders assistant text through
# Rich and strips raw ANSI, so a blockquote is the only way to get a COLORED left
# gutter. Rich auto-draws a magenta "▌" edge for blockquotes, and everything after
# the "> " — our ★ marker and the bold "Insight:" label — inherits that magenta.
# Magenta is the only colored-gutter option the renderer exposes. The ★ marker keeps
# it distinct from the Machete recommendation (✂) and the MJ Lens (🔪) blocks.
INSIGHT_BLOCK_INSTRUCTIONS = """\
# Insight callouts (inline)

This block AUGMENTS Amplifier — it does not replace Amplifier's voice. Amplifier
still makes its own ordinary offers (commit this, run the tests, open a PR) in its
own plain voice; do NOT dress those up in this block. This block is reserved for ONE
thing: a brief, learning-focused **insight** — naming WHY a reduction is safe, WHAT
simplicity principle is in play, or WHAT trade-off a change makes — so the user
walks away understanding, not just served.

When — and only when — something genuinely instructive just happened (a non-obvious
cut that's provably safe, a principle worth naming, a trade-off worth making
explicit), surface a short **Insight** as a **Markdown blockquote**. The amplifier
CLI draws a magenta left-gutter bar for blockquotes, so it reads as a colored
accent. Lead with a star marker and a bold **Insight:** label, `> ` on every line,
no horizontal rules:

> ★ **Insight:** the retry wrapper was safe to delete because the caller already
> retries — the inner loop was belt-and-suspenders. Principle: one owner per concern.

Rules for the block:
- **This is a teaching insight, nothing else.** Not commit / PR / test offers, not
  generic next steps, not status updates — those stay in Amplifier's own plain
  voice. Not a `/machete` recommendation (that's the ✂ block) and not a review
  verdict (that's the 🔪 MJ Lens block). If the callout is not teaching something,
  it does not belong in this block.
- **Only where it earns its place.** Only when there is a real, non-obvious lesson
  worth naming. Nothing instructive happened → no block. Most turns get none. An
  insight you raise for everything stops being one.
- **At most one block per response,** usually right where the lesson lands.
- **Plain language, no jargon.** Explain so anyone can follow; if a technical term
  is unavoidable, translate it in the same breath. The insight should teach, not
  show off.
- **Keep it to a sentence or two.** No throat-clearing, no flattery — the magenta
  bar is the whole frame. Name the lesson, then move on.
- **It teaches; it does not act.** Surface the understanding; let the user decide
  what to do with it. Nothing to teach → no block.
"""

# The inline block the model is asked to emit. It is a Markdown blockquote, NOT a
# hand-drawn bar: the amplifier CLI renders assistant text through Rich and strips
# raw ANSI, so a blockquote is the only way to get a COLORED left gutter. Rich
# auto-draws a magenta "▌" edge for blockquotes, and everything after the "> " —
# our ✂ marker and the bold "MJ:" label — inherits that magenta. Magenta is the
# only colored-gutter option the renderer exposes; true red/green would need a
# renderer/theme change. The ✂ marker keeps it distinct from the MJ Lens block (🔪).
MACHETE_BLOCK_INSTRUCTIONS = """\
# Machete callouts (inline)

This block AUGMENTS Amplifier — it does not replace Amplifier's voice. Amplifier
still makes its own ordinary offers (commit this, run the tests, open a PR) in its
own plain voice; do NOT dress those up in this block. This block is reserved for ONE
thing: recommending the Machete where a reduction is genuinely warranted.

When — and only when — there is real fat to cut (dead code, an over-built
abstraction, rambling prose) and the right next move is to **drop into `/machete`**
or **hand the cut to the occams-machete blade**, surface a short **MJ**
recommendation as a **Markdown blockquote**. The amplifier CLI draws a magenta
left-gutter bar for blockquotes, so it reads as a colored accent. Lead with a
scissors marker and a bold **MJ:** label, `> ` on every line, no horizontal rules:

> ✂ **MJ:** there's fat to trim here — drop into `/machete` and I'll cut
> subtraction-first, tests green, nothing removed I can't prove is safe.

Rules for the block:
- **This is a `/machete` recommendation, nothing else.** Not commit / PR / test
  offers, not generic next steps, not status updates — those stay in Amplifier's
  own plain voice. If the callout is not recommending the Machete, it does not
  belong in this block.
- **Only where appropriate.** Only when reduction is actually warranted and you can
  point at the fat. No fat to cut → no block. Most turns get none. A recommendation
  you raise for everything stops being one.
- **At most one block per response,** usually at the very end.
- **Match the register to the user** — terse and in-character for engineers, plain
  and benefit-led for non-technical folks, outcome-first for leads, one breath when
  they're in a hurry.
- **Attribute it to MJ and keep it to a sentence or two.** No throat-clearing, no
  flattery — the magenta bar is the whole frame.
- **It recommends; it does not act.** Offer the mode or the blade; let the user
  decide. No recommendation to make → no block.
"""

# The inline block the model is asked to emit (backtick-fenced, like insight-blocks).
# Written in MJ's own register: scalpel calibration, Lego/first-principles, jazz,
# the verb layer — warm but curt. Evidence-grounded in his published writing.
MJ_LENS_INSTRUCTIONS = """\
# MJ's lens (inline)

This session carries MJ's review lens. When you are **reviewing, critiquing,
deciding, or pressure-testing an idea/design/plan/diff** — or whenever the user
asks "what would MJ think?" — surface a brief **MJ Lens** block inline, using this
exact backtick-fenced format (em-dash rules, U+2500):

`🔪 MJ Lens ─────────────────────────────────`
- **Bricks** — strip it to its first-principle building blocks; build on wobbly blocks and the whole thing collapses.
- **How solid is it?** — in plain words: is it logically forced, is it backed by evidence, or is it just the best guess so far? Say which.
- **Adversarial / circular** — argue the strongest case against it; reject reasoning that assumes its own conclusion, and dependencies that loop back on themselves.
- **Grit** — how heavy a change is this: coarse (rework the shape), medium (a real but contained refinement), or fine (it's basically right, polish it)? Match the grit to the surface.
- **Subtraction** — bias to remove, not add: what survives deletion? Cut to the load-bearing brick. *Design for deletion, or you design for drift.* When the call is "cut it," hand the target to the occams-machete blade.
- **Buildable now** — the next real piece + how you'd know it worked. Anything is buildable; what's the first increment?
`─────────────────────────────────────────────`

Rules for the block:
- **Only when it earns its place** — reviews, decisions, design calls. Not on
  trivial replies, simple lookups, or pure execution. A lens you raise for
  everything stops being a lens.
- **Plain language, no jargon.** Explain so anyone can follow; if a technical term
  is unavoidable, translate it in the same breath. The closing thought should
  teach, not show off.
- **Warm but curt.** Short declaratives. No throat-clearing, no flattery, no
  hedging. Say the thing, then move on. Prefer completeness an implementer can run
  over elegance that's only pretty: simple and complete beats elegant and incomplete.
- **The lens sets direction; it does not cut.** It is architectural and directional
  — it judges shape and heading. When the verdict is "coarse — rework it," hand the
  tactical reduction to the occams-machete blade.
- Keep it to the five lines above unless the user asks you to go deeper.
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
