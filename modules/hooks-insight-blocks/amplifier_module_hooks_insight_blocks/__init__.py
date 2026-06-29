"""hooks-insight-blocks — surface a short educational insight as an inline block.

A contemporary, bundle-native upgrade of amplifier-module-hooks-insight-blocks.
The upstream module taught the model to emit `★ Insight ─────` blocks fenced with
U+2500 horizontal rules. That no longer renders as a colored accent: the amplifier
CLI pipes assistant text through Rich and strips raw ANSI, so the hand-drawn rule
reads as plain grey text. This version keeps the upstream's PURPOSE — brief,
learning-focused insights — but adopts this bundle's contemporary mechanism: a
Markdown **blockquote**, which Rich paints with a magenta left gutter (the only
renderer-native colored-accent path the CLI exposes). It mirrors the sibling
hooks-machete-blocks / hooks-mj-lens contract: on session start we inject a system
instruction; the model's own text IS the block; there is no special renderer.
Fail-open — any error degrades to a no-op rather than breaking the session.

Themed to the bundle's mission (reduction / ruthless simplicity): the insight names
WHY a cut is safe, WHAT principle is in play, or WHAT trade-off is being made — a
teaching moment, not a status update. This AUGMENTS Amplifier; it does not replace
its voice. Amplifier's ordinary offers (commit, run the tests, open a PR) stay in
Amplifier's own plain voice. The ★ marker keeps it distinct from the Machete
recommendation block (✂) and the MJ Lens review block (🔪).
"""

import logging
from typing import Any

from amplifier_core import HookResult

logger = logging.getLogger(__name__)

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


def _build_instructions(config: dict[str, Any]) -> str:
    """Assemble the injection string. Isolated so failures here stay contained."""
    extra = config.get("extra_instructions")
    if isinstance(extra, str) and extra.strip():
        return INSIGHT_BLOCK_INSTRUCTIONS + "\n" + extra.strip() + "\n"
    return INSIGHT_BLOCK_INSTRUCTIONS


async def mount(
    coordinator: Any, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Register a session:start handler that injects the insight-block instructions.

    Returns a metadata dict. Honors `enabled` (default True) and `priority`
    (default 50) config keys, matching the insight-blocks / hooks-mj-lens /
    hooks-machete-blocks convention.
    """
    config = config or {}

    if not config.get("enabled", True):
        logger.info("hooks-insight-blocks disabled via config")
        return {
            "name": "hooks-insight-blocks",
            "version": "0.1.0",
            "provides": [],
            "enabled": False,
        }

    priority = int(config.get("priority", 50))

    async def insight_blocks_session_start(
        event: str, data: dict[str, Any]
    ) -> HookResult:
        try:
            instructions = _build_instructions(config)
            return HookResult(
                action="inject_context",
                context_injection=instructions,
                context_injection_role="system",
                ephemeral=False,
            )
        except Exception:  # fail-open: never break a session over a briefing
            logger.exception(
                "hooks-insight-blocks: injection failed; degrading to no-op"
            )
            return HookResult(action="continue")

    coordinator.hooks.register(
        event="session:start",
        handler=insight_blocks_session_start,
        priority=priority,
        name="hooks-insight-blocks",
    )
    logger.info(
        "hooks-insight-blocks mounted: educational insights will surface inline"
    )
    return {
        "name": "hooks-insight-blocks",
        "version": "0.1.0",
        "provides": ["insight-block-injection"],
    }
