# Occam's Machete (awareness)

This bundle gives you a decisive code-and-prose **reducer**. It is the doer that
complements two advisors you may also have: **Cranky Old Sam** (simplicity
verdicts) and the **Crusty Old Engineer** (consequence checks). Sam and Crusty
*judge*. The Machete *cuts*.

## Three ways in

| Surface | Use it when | How |
|---|---|---|
| **Skill** | You want the verdict + the reduction plan in the Machete's voice, in the current session. | `load_skill(skill_name="occams-machete")` |
| **Agent** | You want the cut actually *made* — files edited, tests run, a diff + body count returned. | `delegate(agent="occams-machete:occams-machete", instruction="...", context_depth="recent")` |
| **Mode** | You're doing a sustained slash-and-burn pass and want the whole session biased toward subtraction. | `/machete` (or `mode(operation="set", name="machete")`) |

## When to reach for it

Trigger on intent like: *refactor for simplicity*, *reduce this*, *delete the
dead code*, *inline this abstraction*, *collapse these layers*, *this got out of
hand*, *tighten this writeup*, *too much thought diarrhea*, *make it elegant*.

## When NOT to

The Machete **removes; it does not add**. For "what should I build?", "should
this exist?", or new-design questions, route to a brainstorm, to Cranky Old Sam,
or to the Crusty Old Engineer. Invite the Machete once there is something concrete
to cut.

## Where it sits in your workflow

The Machete lives at the **tail of the build arc** and the **front of the
reduction arc** — reach for it when something has already accreted:

- After a superpowers `/execute-plan` (or any build sprint) has run for a while
  → a reduction pass keeps velocity from turning into sprawl. Superpowers adds;
  the Machete subtracts.
- After `zen-architect` REVIEW flags complexity → the Machete is what actually
  removes it (REVIEW advises; it does not cut).
- After Cranky Old Sam / the Crusty Old Engineer return "yes, this is over-built"
  → the Machete performs the extraction the advisors won't.

## Recipes

For sustained or auditable passes, the bundle ships two recipes (run via the
`recipes` tool):

- `occams-machete:recipes/reduce-target.yaml` — single target: records a green
  baseline, runs the cut, re-verifies. Needs a `target_path`.
- `occams-machete:recipes/panel-then-cut.yaml` — the **panel pipeline**: the
  three-lens review (Sam's "why exist?", Crusty's "what cost?", the Machete's
  "what comes out?") produces a verdict, then a **human approval gate**, then the
  cut lands and is verified. Needs a `target_path`. Use this when the edits are
  irreversible enough that you want eyes on the plan before the blade.

Reach for a recipe only when you want the approval gate or the recorded
before/after baseline. For an ordinary cut, just delegate to the agent — it
already runs the full inventory → cut → verify loop on its own.

## The one rule that keeps it from being a wood chipper

Every cut preserves behavior and keeps the tests green — one reversible stroke at
a time. If you delegate to the agent, it will refuse to remove behavior it can't
prove it preserved. That refusal is a feature; don't override it without thinking.
