# MJ's bench — which lens owns which question

Loaded on demand, not always-on. Four lenses, one question each. They are useful
because they disagree, and they disagree because none of them is allowed to
answer another's question.

| Lens | Owns | Reach for it |
|---|---|---|
| `mj:goal-keeper` | *Is this what was asked for?* | Before claiming done, before a PR, or after a request has been through enough turns to drift |
| `mj:mj-reviewer` | *Is this pointed the right way, and how heavy a change does it really need?* | Before committing to a direction |
| `mj:crusty-old-engineer` | *What breaks, and what will it cost later?* | Before shipping, or before trusting an "it's fixed" claim |
| `mj:occams-machete` | *What comes out?* | When the answer is "remove it" — this one edits files |

Only the last one writes. The first three are advisory by contract.

## Picking between them

The common mistake is reaching for a *quality* lens when the problem is
*conformance*, or the reverse.

- Work looks good but you're unsure it's the right shape → **mj-reviewer**.
- Work looks good and you're about to ship it → **crusty-old-engineer**.
- Work looks good and you're about to say "done" → **goal-keeper**. This is the
  one people skip. The other three will all bless excellent work that answers a
  question nobody asked.
- Something should be smaller → **occams-machete**, or `/machete` mode.

Two surfaces carry a lens without a delegation: `/mj` mode (review posture,
mutation blocked) and `load_skill("mj-lens")` (the review discipline applied to
the *current conversation* — the mj-reviewer agent forks and cannot see it).

## What the bench deliberately does NOT do

**It does not convene all lenses at once.** This repo ran that experiment
(`evaluation/occams-vs-council/`): the heavier multi-lens council never paid for
itself — it tied at best and lost to its own verbosity, and the single blade held its
own across the board. Reach for the lens the question needs. The one
pipeline that convenes more than one, `panel-then-cut`, uses exactly two and puts
a human between them.

**It does not generate.** Every lens here judges or reduces existing work. For
"what should we build," go to a brainstorm; come back when there is something
concrete.

**It does not decide.** Every advisory lens ends in a recommendation, and every
recipe that acts on one has a human approval gate. An advisor's refusal is not
the requester's decision — which is precisely what `goal-keeper` exists to catch.

## The failure mode this bench was built around

A reviewer argues against something, the reasoning is good, the thing is never
built, and everyone moves on believing the request was handled. The work is
excellent. The request is unmet. Quality lenses cannot see this, because nothing
about the delivered work is wrong — it is simply not the thing that was asked
for.

That is why `goal-keeper` judges conformance and refuses to judge merit, and why
it treats an unratified substitution as undelivered no matter how sound the
argument for it was.
