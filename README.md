# amplifier-bundle-occams-machete

> *Entia non sunt multiplicanda praeter necessitatem.*
> Entities should not be multiplied beyond necessity.
> — William of Ockham, who would have loved `git rm`.

A grumpy-craftsman Amplifier bundle whose entire job is to make things **smaller,
leaner, and more elegant**: reduce code, refactor toward simplicity, and stop
**thought diarrhea** — the rambling, hedging, gold-plated sprawl that piles up
when smart people keep typing past the point they were done.

It is the third member of a panel:

| Sibling | Asks | Produces |
|---|---|---|
| **Cranky Old Sam** | "Why does this exist at all?" | A simplicity verdict. |
| **Crusty Old Engineer** | "What will this cost you later?" | A risk assessment. |
| **Occam's Machete** *(this bundle)* | "Fine. It's out." | A **smaller codebase, tests green** — the actual cut. |

Sam and Crusty *review*. They were never going to touch your code. The Machete is
the missing piece: the one that picks up the blade and **does the removing** —
safely, one reversible stroke at a time, tests green on both sides.

## Why a bundle and not just another skill?

Because the gap Sam and Crusty leave is **execution**. A skill can only advise the
current session. This bundle ships three things so the persona can both *judge*
and *act*:

- A **skill** — the judgment and voice (advice in the current session).
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
│   └── occams-machete.md          # the executioner: actually performs the cuts
├── modes/
│   └── machete.md                 # /machete — reduction-only working posture
├── recipes/
│   ├── reduce-target.yaml         # baseline → cut → verify (single target)
│   └── panel-then-cut.yaml        # review → APPROVAL GATE → cut (the panel, wired)
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

**Get the verdict + plan (in-session):**
```
load_skill(skill_name="occams-machete")
```

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
whole-file deletes ask first.

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
land. `panel-then-cut` is the three siblings wired into one auditable pipeline —
Sam's "why exist?", Crusty's "what cost?", then the Machete's blade, with you
holding the gate in between.

## The panel, made real

The three siblings are not rivals; they're a pipeline:

| | Question | Output |
|---|---|---|
| **Cranky Old Sam** | "Why does this exist at all?" | A simplicity verdict. |
| **Crusty Old Engineer** | "What will this cost you later?" | A risk assessment. |
| **Occam's Machete** *(this bundle)* | "Fine. It's out." | A smaller codebase, tests green. |

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

- Design or add features. It removes; full stop. (That's Sam/Crusty/brainstorm.)
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

## Lineage

Modeled after, and built to complete, the `cranky-old-sam` and
`crusty-old-engineer` skills. Same grumpy-craftsman DNA, sharper edge, and —
unlike its siblings — a willingness to actually pick up the tool.
