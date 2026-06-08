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

## The one rule that keeps it from being a wood chipper

Every cut preserves behavior and keeps the tests green — one reversible stroke at
a time. If you delegate to the agent, it will refuse to remove behavior it can't
prove it preserved. That refusal is a feature; don't override it without thinking.
