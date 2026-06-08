# amplifier-bundle-occams-machete

> *Entia non sunt multiplicanda praeter necessitatem.*
> Entities should not be multiplied beyond necessity.
> — William of Ockham, who would have loved `git rm`.

A grumpy-craftsman Amplifier bundle whose entire job is to make things **smaller,
leaner, and more elegant**: reduce code, refactor toward simplicity, and stop
**thought diarrhea** — the rambling, hedging, gold-plated sprawl that piles up
when smart people keep typing past the point they were done.

Most simplicity tools only *advise* — they hand you a verdict and a risk
assessment, then leave the actual work to you:

| Asks | Produces |
|---|---|
| "Why does this exist?" | a simplicity verdict (advice) |
| "What will it cost later?" | a risk assessment (advice) |
| **"Fine. It's out."** *(this bundle)* | a **smaller codebase, tests green** — the actual cut |

This bundle is the missing piece: the one that picks up the blade and **does the
removing** — safely, one reversible stroke at a time, tests green on both sides.

## Why a bundle and not just another skill?

Because the gap advice leaves is **execution**. A skill can only advise the
current session. This bundle ships three things so the persona can both *judge*
and *act*:

- A **skill** — the judgment and voice (the substrate the agent and mode carry).
- An **agent** — the executioner that reads, edits, runs tests, and returns a diff.
- A **mode** — a sustained reduction posture for a whole working session.

## What's inside

```
amplifier-bundle-occams-machete/
├── bundle.md                      # bundle root (thin router → foundation + behavior)
├── README.md                      # you are here
├── behaviors/
│   └── occams-machete.yaml        # wires the agent, skill, and /machete mode
├── skills/
│   └── occams-machete/
│       └── SKILL.md               # the persona: judgment + voice + discipline
├── agents/
│   ├── occams-machete.md          # the executioner: actually performs the cuts
│   └── mj-reviewer.md             # the MJ lens: "what would MJ think about this?"
├── modes/
│   └── machete.md                 # /machete — reduction-only working posture
├── recipes/
│   ├── reduce-target.yaml         # baseline → cut → verify (single target)
│   └── panel-then-cut.yaml        # multi-lens review → APPROVAL GATE → cut
├── context/
│   └── machete-awareness.md       # thin routing for the root session
├── bundle.dot                     # composition diagram (v3 convention)
└── bundle.png                     # rendered diagram
```

Yes, that's deliberately small. A bundle that preaches ruthless simplicity and
then ships forty files would be a punchline. This one eats its own cooking — the
two recipes earn their place by adding what plain delegation can't (a recorded
before/after baseline, and a human approval gate before irreversible edits land).

## Usage

**Get the verdict + plan (no diff yet):** enter `/machete`, or ask the
`occams-machete` agent for a *plan-only* pass ("propose the cuts, don't edit"). The
persona's judgment is injected into both — there is no separate skill to load.

**Make the cut (delegate to the executioner):**
```
delegate(
  agent="occams-machete:occams-machete",
  instruction="Reduce src/router.py — it has a six-stage middleware pipeline and a one-implementation handler registry. Preserve behavior, keep tests green.",
  context_depth="recent",
)
```

**Spend a whole session cutting:**
```
/machete
```
In machete mode, subtraction is the default move, new files are treated as
suspects (`write_file` warns), shell is surfaced once (`bash` warns), and
whole-file deletes ask first. It **cuts aggressively but never recklessly** — the
mode's tool policies and the discipline below are exactly the guardrails that make
that phrase true rather than marketing.

**Run a guarded reduction pass (recipes):**
```
# single target: records a green baseline, cuts, re-verifies
execute recipe occams-machete:recipes/reduce-target.yaml with target_path=src/router.py

# the panel: three-lens review → human approval gate → cut → verify
execute recipe occams-machete:recipes/panel-then-cut.yaml with target_path=src/router.py
```
The agent already runs its own inventory → cut → verify loop, so reach for a
recipe only when you want what plain delegation can't give you: a recorded
before/after baseline, or a **human approval gate** before irreversible edits
land. `panel-then-cut` wires a multi-lens advisory review into one auditable
pipeline — "why does it exist?", "what will it cost?", then the Machete's blade,
with you holding the gate in between.

## The pipeline, made real

Advice and action are not rivals; they're a pipeline (the table up top).
`recipes/panel-then-cut.yaml` turns that table from a metaphor into a runnable,
gated workflow. The composition is also drawn in `bundle.png` (source:
`bundle.dot`, v3 convention).

## The discipline (what keeps it a machete, not a wood chipper)

Aggression without discipline is just damage. Every cut obeys:

1. **Name the job before the blade** — state what must still be true; preserve behavior.
2. **Green on both sides** — tests pass before and after; no coverage means *characterize first*.
3. **One stroke, one commit** — each removal is independent and reversible.
4. **Accidental complexity only** — the irreducible difficulty of the real problem stays.
5. **No new entities** — it inlines, collapses, and deletes. It does not add frameworks "to tidy up."

Every reduction ends with a **body count** — `-214 lines, -3 files, -2 abstractions,
tests green`. Numbers, not adjectives.

## What it will refuse to do

- Design or add features. It removes; full stop. (That's brainstorming/design — a different job.)
- Cut behavior. Smaller-that-does-less is a regression, not a win.
- Remove something it can't prove it preserved. Boldness without evidence is just risk with good PR.
- Trade ten readable lines for one cryptic one. It reduces *confusion*, not only line count.
- Shame the author. The accretion is the defendant; the person is a witness.

## Status

`v0.1.0` — wired and validated. The persona, agent, mode, and routing are
written, and the bundle has been converted to the Amplifier-native thin-bundle
pattern:

- `bundle.md` is a thin router: `includes:` foundation + `behaviors/occams-machete.yaml`.
- The behavior wires the agent (`agents.include`), the persona skill
  (`tool-skills` with a `source:`), and the `/machete` mode (the modes system:
  the modes behavior + `hooks-mode` `search_paths` + `tool-mode`).

To re-validate after changes, run `validate-bundle-repo`, consult
`foundation:foundation-expert`, or run it through **bundlewizard**
(`/bundle-verify`) for a three-level audit.

## "What would MJ think about this?"

This bundle is MJ's machete — so it also carries **MJ's lens**. Ask *"what would MJ
think about this?"* (about an idea, design, plan, argument, or diff) and the
`mj-reviewer` agent answers the way MJ actually reviews — built from evidence mined
across **305 of his own sessions**, graded by confidence, and honest about what's
corroborated vs. self-reported (it won't fabricate corroboration — MJ would catch it).

The lens and the blade work on **different axes**, which is why both exist:

- **`mj-reviewer` is architectural and directional** — it judges *shape*, *heading*,
  and *how heavy a change is needed*, in plain language. It sets the direction.
- **`occams-machete` is tactical and action** — it executes the concrete reduction
  on a concrete target. It carries out the cut.

Direction vs. execution — not two copies of the same thing.

MJ's review runs seven moves, all in **plain language, no jargon**: **first
principles** → a plain read of **how solid the claim is** (is it logically forced,
backed by evidence, or just the best guess so far?) → an **adversarial +
anti-circular** pass → a **grit call** (how heavy a change: **coarse** /
**medium** / **fine** — heavy/medium/light; coarse hands off to the machete) →
a **buildable-now** next step (*anything is buildable*) → **completeness over
elegance** when they conflict → a closing that's **warm, blunt, brief, and
pedagogical** — it teaches the *why*, not just the ruling.

```
delegate(agent="occams-machete:mj-reviewer",
         instruction="What would MJ think about <idea/design/plan/diff>?")
```

Every session that loads this bundle is surfaced the lens automatically (via the
always-on `context/mj-lens-awareness.md`); the full evidence-graded profile lives at
`context/mj-profile.md` and is loaded on demand. The reviewer **grades**; when the
call is "coarse — cut it," the blade does the cutting.

## Lineage

Cut from the same grumpy-craftsman cloth as the simplicity advisors that inspired
it — same DNA, sharper edge, and, unlike a pure advisor, a willingness to actually
pick up the tool.
