"""hooks-machete-blocks — surface the `/machete` recommendation as an inline block.

Mirrors the mechanism of amplifier-module-hooks-insight-blocks (and this bundle's
sibling hooks-mj-lens): on session start we inject a system instruction asking the
model to set off ONE specific thing — a recommendation to use the Machete (drop
into `/machete`, or hand the cut to the occams-machete blade) where a reduction is
genuinely warranted — as a Markdown blockquote so it reads as a colored accent.
There is no special renderer — the model's text IS the block. Fail-open: any error
degrades to a no-op rather than breaking the session.

This AUGMENTS Amplifier; it does not replace its voice. Amplifier's ordinary offers
(commit, run the tests, open a PR) stay in Amplifier's own plain voice — only the
Machete recommendation gets this block, and only where appropriate (not every turn).
"""

import logging
from typing import Any

from amplifier_core import HookResult

logger = logging.getLogger(__name__)

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


def _build_instructions(config: dict[str, Any]) -> str:
    """Assemble the injection string. Isolated so failures here stay contained."""
    extra = config.get("extra_instructions")
    if isinstance(extra, str) and extra.strip():
        return MACHETE_BLOCK_INSTRUCTIONS + "\n" + extra.strip() + "\n"
    return MACHETE_BLOCK_INSTRUCTIONS


async def mount(
    coordinator: Any, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Register a session:start handler that injects the Machete-block instructions.

    Returns a metadata dict. Honors `enabled` (default True) and `priority`
    (default 50) config keys, matching the insight-blocks / hooks-mj-lens convention.
    """
    config = config or {}

    if not config.get("enabled", True):
        logger.info("hooks-machete-blocks disabled via config")
        return {
            "name": "hooks-machete-blocks",
            "version": "0.1.0",
            "provides": [],
            "enabled": False,
        }

    priority = int(config.get("priority", 50))

    async def machete_blocks_session_start(
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
                "hooks-machete-blocks: injection failed; degrading to no-op"
            )
            return HookResult(action="continue")

    coordinator.hooks.register(
        event="session:start",
        handler=machete_blocks_session_start,
        priority=priority,
        name="hooks-machete-blocks",
    )
    logger.info(
        "hooks-machete-blocks mounted: notable Machete callouts will surface inline"
    )
    return {
        "name": "hooks-machete-blocks",
        "version": "0.1.0",
        "provides": ["machete-block-injection"],
    }
