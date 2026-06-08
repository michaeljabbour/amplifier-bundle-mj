# Occam's Machete (awareness)

A decisive code-and-prose **reducer** — the doer that complements two advisors
you may also have: **Cranky Old Sam** (simplicity verdicts) and the **Crusty Old
Engineer** (consequence checks). Sam and Crusty *judge*. The Machete *cuts*.

## Three ways in

| Surface | Use it when | How |
|---|---|---|
| **Skill (judgment + voice)** | You want the verdict + reduction plan in the Machete's voice. | Injected into the agent and `/machete` mode — ask the agent for a *plan-only* pass, or enter `/machete`. |
| **Agent** | You want the cut actually *made* — files edited, tests run, a diff + body count returned. | `delegate(agent="occams-machete:occams-machete", instruction="...", context_depth="recent")` |
| **Mode** | You're doing a sustained slash-and-burn pass and want the whole session biased toward subtraction. | `/machete` (or `mode(operation="set", name="machete")`) |

For sustained or auditable passes the bundle also ships two recipes
(`recipes/reduce-target.yaml`, `recipes/panel-then-cut.yaml`); reach for them
only when you want an approval gate or a recorded before/after baseline. For an
ordinary cut, just delegate to the agent.

## When to reach for it

Trigger on intent like: *refactor for simplicity*, *reduce this*, *delete the
dead code*, *inline this abstraction*, *collapse these layers*, *this got out of
hand*, *tighten this writeup*, *too much thought diarrhea*, *make it elegant*.

## When NOT to

The Machete **removes; it does not add**. For "what should I build?", "should
this exist?", or new-design questions, route to a brainstorm, to Cranky Old Sam,
or to the Crusty Old Engineer. Invite the Machete once there is something concrete
to cut. The one rule that keeps it from being a wood chipper: every cut preserves
behavior and keeps the tests green, one reversible stroke at a time.
