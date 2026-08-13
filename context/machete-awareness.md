# Occam's Machete (awareness)

A code-and-prose **reducer** that *cuts*, where most simplicity tools only advise.

## Three ways in
- **Agent** — the cut actually made (files edited, tests run, diff, and a tally of
  what came out):
  `delegate(agent="mj:occams-machete", instruction="...")`
- **Mode** — a sustained pass biased toward removing rather than adding: `/machete`
- **Skill** — the verdict and plan in the Machete's voice, no diff yet; carried by
  the agent and `/machete` (ask for a *plan-only* pass).

Reach for it on intent like *reduce this*, *delete the dead code*, *inline this
abstraction*, *collapse these layers*, *this got out of hand*, *tighten this
writeup*, *make it elegant*.

Two recipes add an approval gate or a recorded before/after baseline to a cut:
`recipes/reduce-target.yaml` and `recipes/panel-then-cut.yaml`. A third,
`recipes/preflight-guard.yaml`, runs the reliability guard below over a changeset
— no gate, no baseline.

## Guard before you ship
The **Crusty Old Engineer**
(`delegate(agent="mj:crusty-old-engineer")`) is the reliability guard.
It catches what will break — broken contracts, stale references, code that fails at
load time, errors swallowed in silence — and reports what's actually broken, what
will cost you later, and a ship / don't-ship call. Reach for it, or the
`preflight-guard` recipe, before opening a PR or trusting an "it's fixed" claim. It
advises; it doesn't cut (that's `occams-machete`) or set direction (that's
`mj-reviewer`).

## Offer it, don't trim silently
When a task is clearly about removing something, offer `/machete` once, in one
sentence, in the user's own words. The session hook formats that as the magenta
**MJ** callout.

## When NOT to
It **removes; it does not add**. For "should this exist?" or new-design questions,
route to a brainstorm. Invite it once there's something concrete to cut — and every
cut preserves behavior and keeps the tests green.
