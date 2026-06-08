"""hooks-mj-lens — surface MJ's review lens as an inline insight block.

Mirrors the mechanism of amplifier-module-hooks-insight-blocks: on session start
we inject a system instruction that asks the model to emit a short, backtick-fenced
"MJ Lens" block inline in its own prose whenever it is reviewing, deciding, or
pressure-testing an idea. There is no special renderer — the model's text IS the
block. Fail-open: any error degrades to a no-op rather than breaking the session.
"""

import logging
from typing import Any

from amplifier_core import HookResult

logger = logging.getLogger(__name__)

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
- **Bricks** — strip it to first-principle Lego bricks; build on wobbly bricks and castles collapse.
- **Grade** — call it honestly: deductively (entailed?), inductively (evidenced?), abductively (just the best frame so far?).
- **Adversarial / circular** — steelman the strongest takedown; reject circular reasoning and circular dependence.
- **Scalpel** — which blade? No. 15 (fine — it's basically right, polish it) or No. 20 (deep — rework the shape)? Match the cut to the tissue.
- **Buildable now** — the next real brick + how you'd know it worked. Anything is buildable; what's the first increment?
`─────────────────────────────────────────────`

Rules for the block:
- **Only when it earns its place** — reviews, decisions, design calls. Not on
  trivial replies, simple lookups, or pure execution. A lens you raise for
  everything stops being a lens.
- **Warm but curt.** Short declaratives. No throat-clearing, no flattery, no
  hedging. Say the thing, then move on. Prefer completeness an implementer can run
  over elegance that's only pretty: simple and complete beats elegant and incomplete.
- **The lens grades; it does not cut.** When the verdict is "No. 20 — rework it,"
  hand the actual reduction to the occams-machete blade or the mj-reviewer agent.
- Keep it to the five lines above unless the user asks you to go deeper.
"""


def _build_instructions(config: dict[str, Any]) -> str:
    """Assemble the injection string. Isolated so failures here stay contained."""
    extra = config.get("extra_instructions")
    if isinstance(extra, str) and extra.strip():
        return MJ_LENS_INSTRUCTIONS + "\n" + extra.strip() + "\n"
    return MJ_LENS_INSTRUCTIONS


async def mount(
    coordinator: Any, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Register a session:start handler that injects the MJ-lens instructions.

    Returns a metadata dict. Honors `enabled` (default True) and `priority`
    (default 50) config keys, matching the insight-blocks convention.
    """
    config = config or {}

    if not config.get("enabled", True):
        logger.info("hooks-mj-lens disabled via config")
        return {
            "name": "hooks-mj-lens",
            "version": "0.1.0",
            "provides": [],
            "enabled": False,
        }

    priority = int(config.get("priority", 50))

    async def mj_lens_session_start(event: str, data: dict[str, Any]) -> HookResult:
        try:
            instructions = _build_instructions(config)
            return HookResult(
                action="inject_context",
                context_injection=instructions,
                context_injection_role="system",
                ephemeral=False,
            )
        except Exception:  # fail-open: never break a session over a briefing
            logger.exception("hooks-mj-lens: injection failed; degrading to no-op")
            return HookResult(action="continue")

    coordinator.hooks.register(
        event="session:start",
        handler=mj_lens_session_start,
        priority=priority,
        name="hooks-mj-lens",
    )
    logger.info(
        "hooks-mj-lens mounted: MJ lens will surface inline on review/decision turns"
    )
    return {
        "name": "hooks-mj-lens",
        "version": "0.1.0",
        "provides": ["mj-lens-injection"],
    }
