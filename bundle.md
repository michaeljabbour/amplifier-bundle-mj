---
bundle:
  name: occams-machete
  version: 0.1.0
  description: >-
    A decisive code-and-prose reducer. Where most simplicity tools only advise, the
    Machete cuts — safely, one reversible stroke at a time, tests green on both
    sides. Ships a persona skill, an executioner agent, an MJ-lens reviewer ("what
    would MJ think?"), and a /machete reduction mode.

# Thin bundle: inherit foundation (filesystem, bash, grep, LSP, etc.), then add
# our unique capability via the behavior. The behavior wires the skill, the
# agent, and the /machete mode (modes system: hooks-mode + tool-mode).
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: occams-machete:behaviors/occams-machete
---

# Occam's Machete

The simplest explanation is usually right. The simplest code usually is too.
This bundle is the blade that gets you there.

Most simplicity tools only *advise* — they ask *"why does this exist?"* and *"what
will it cost later?"* and hand you the verdict. The **Machete** does the thing they
won't: it picks up the blade and **removes the thing** — safely, one reversible
stroke at a time, tests green on both sides.

It cuts code. It cuts plans. It cuts thought diarrhea — the rambling, hedging,
restated, gold-plated sprawl that accumulates when smart people keep typing past
the point they were done.

## What's in the box

| Capability | What it is | Reach for it when |
|---|---|---|
| The persona skill (judgment + voice) | Diagnoses bloat and proposes the smaller version, in the Machete's voice. It's injected into the agent and `/machete` mode — ask the agent for a *plan-only* pass to get it. | You want the verdict and the plan, not the diff yet. |
| `delegate(agent="occams-machete")` | The executioner — *tactical, action*. Reads, reduces, runs the tests, returns a body count. | You want the cut *made*, not just recommended. |
| `/machete` mode | A reduction-only working posture: subtraction is the default, new files are treated as suspects. | You're doing a sustained slash-and-burn pass on a file or module. |
| `delegate(agent="occams-machete:mj-reviewer")` | The MJ lens — *architectural, directional*. Judges shape, heading, and how heavy a change is needed, in plain language. | You want **direction** or a gut-check ("what would MJ think?"), not the cut itself. |

The first three surfaces *do the reduction* (tactical); the MJ lens *sets direction*
(architectural). Two axes — execution vs. direction — not duplicates.

Start at `README.md`. The Machete would tell you to read less and delete more,
but it wrote you a README anyway, because it's not a savage.
