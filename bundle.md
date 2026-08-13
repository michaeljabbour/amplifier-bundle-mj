---
bundle:
  name: mj
  version: 0.2.0
  description: >-
    MJ's review bench — three lenses that judge work on different axes, and one
    of them cuts. Occam's Machete removes complexity (tactical); the MJ lens sets
    direction ("what would MJ think?"); the Crusty Old Engineer catches what
    breaks before you ship. Plus a persona skill and a /machete reduction mode.

# Thin bundle: inherit foundation (filesystem, bash, grep, LSP, etc.), then add
# our unique capability via the behavior. The behavior wires the three agents,
# the skill, and the /machete mode (modes system: hooks-mode + tool-mode).
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: mj:behaviors/mj
---

# MJ's bench

Three lenses. Each owns one question the others skip, and they are useful
precisely because they can disagree.

| Lens | The question it owns | Reach for it when |
|---|---|---|
| **Occam's Machete** — `delegate(agent="mj:occams-machete")` | *What comes out?* | You want the cut **made**, not recommended. Reads, reduces, runs the tests, returns a body count. |
| **The MJ lens** — `delegate(agent="mj:mj-reviewer")` | *Is this pointed the right way, and how heavy a change does it really need?* | You want direction or a gut-check before committing. It sets heading; it doesn't cut. |
| **The Crusty Old Engineer** — `delegate(agent="mj:crusty-old-engineer")` | *What breaks, and what will it cost later?* | Before a PR, or before trusting an "it's fixed" claim. Returns blockers vs risks and a go/no-go. |

Each of the first two lenses also has a **mode** (a sustained working posture)
and a **skill** (the discipline, loadable inline):

| | Mode | Skill |
|---|---|---|
| Machete | `/machete` — subtraction is the default, new files are suspects, irreversible strokes get friction | `occams-machete` — judgment and voice; ask for a *plan-only* pass to get the verdict without the diff |
| MJ lens | `/mj` — review posture with **every mutating tool blocked**, so a review can't drift into editing | `mj-lens` — the review discipline applied to **this conversation** (the agent forks a clean session and can't see it) |

**Recipes** add what plain delegation can't: an approval gate, a recorded
baseline, or a durable decision record.

| Recipe | What it adds |
|---|---|
| `direction-check` | Pressure-test a direction *before* committing. Gate, then writes the call + its counter-argument + your ruling to a decision record. |
| `reduce-target` | Single-target reduction that refuses to cut from a red baseline. |
| `panel-then-cut` | Two independent lenses (guard, then blade), a human gate, then the cut. |
| `preflight-guard` | The reliability guard over a changeset before you ship. |

## Why a bench and not a council

Most review tools only *advise* — they hand you a verdict and leave. One of these
picks up the blade and **removes the thing**, safely, one reversible stroke at a
time, tests green on both sides. It cuts code. It cuts plans. It cuts thought
diarrhea — the rambling, hedging, gold-plated sprawl that accumulates when smart
people keep typing past the point they were done.

They are deliberately *not* all convened by default. This repo ran that
experiment (`evaluation/occams-vs-council/`) and the heavier council never paid
for itself. Reach for the lens the question actually needs; `panel-then-cut`
convenes two of them, in order, with you in the middle.

Start at `README.md`. The Machete would tell you to read less and delete more,
but it wrote you a README anyway, because it's not a savage.
