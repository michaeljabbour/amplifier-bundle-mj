# Occam's Machete (awareness)

A code-and-prose **reducer** that *cuts*, where most simplicity tools only advise.

## Three ways in
- **Agent** — the cut *made* (files edited, tests run, diff + body count):
  `delegate(agent="occams-machete:occams-machete", instruction="...")`
- **Mode** — a sustained pass biased toward subtraction: `/machete`
- **Skill** — the verdict + plan in the Machete's voice, no diff yet; carried by the
  agent and `/machete` (ask for a *plan-only* pass).

Two recipes (`recipes/reduce-target.yaml`, `recipes/panel-then-cut.yaml`) add an
approval gate or a recorded before/after baseline when you want one.

## When to reach for it
Intent like *reduce this*, *delete the dead code*, *inline this abstraction*,
*collapse these layers*, *this got out of hand*, *tighten this writeup*, *make it
elegant*.

## Offer it, don't trim silently
When a task is clearly reduction-shaped, proactively offer `/machete` in one
sentence — attributed to MJ, register-matched, once. The session hook formats that
offer as the magenta **MJ** callout.

## When NOT to
It **removes; it does not add**. For "should this exist?" or new-design questions,
route to a brainstorm. Invite it once there's something concrete to cut — and every
cut preserves behavior and keeps the tests green.
