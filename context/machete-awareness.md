# Occam's Machete (awareness)

A code-and-prose **reducer** that *cuts*, where most simplicity tools only advise.

## Three ways in
- **Agent** — the cut *made* (files edited, tests run, diff + body count):
  `delegate(agent="occams-machete:occams-machete", instruction="...")`
- **Mode** — a sustained pass biased toward subtraction: `/machete`
- **Skill** — the verdict + plan in the Machete's voice, no diff yet; carried by the
  agent and `/machete` (ask for a *plan-only* pass).

Three recipes: `recipes/reduce-target.yaml` and `recipes/panel-then-cut.yaml` add an
approval gate or a recorded before/after baseline to a *reduction*;
`recipes/preflight-guard.yaml` runs the reliability guard over a changeset before
you ship.

## Guard before you ship
Reduction and direction are not the only lenses. The **Crusty Old Engineer**
(`delegate(agent="occams-machete:crusty-old-engineer")`) is the bundle's reliability
guard: it catches **obvious failures** (contract/protocol violations, lagging or
broken refs, load/fork-time fragility, silent failure) and **engineering
anti-patterns** before they ship, returning BLOCKERS vs RISKS and a GO / NO-GO.
Reach for it — or the `preflight-guard` recipe — before opening a PR or trusting an
"it's fixed" claim. It reviews and advises; it does not cut (that's the blade) or set
direction (that's the MJ lens).

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
