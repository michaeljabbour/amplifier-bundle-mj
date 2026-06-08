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
├── occams-machete.md              # bundle root (thin router)
├── README.md                      # you are here
├── skills/
│   └── occams-machete/
│       └── SKILL.md               # the persona: judgment + voice + discipline
├── agents/
│   └── occams-machete.md          # the executioner: actually performs the cuts
├── modes/
│   └── machete.md                 # /machete — reduction-only working posture
└── context/
    └── machete-awareness.md       # thin routing for the root session
```

Yes, that's deliberately small. A bundle that preaches ruthless simplicity and
then ships forty files would be a punchline. This one eats its own cooking.

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
suspects (`write_file` warns), and whole-file deletes ask first.

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

`v0.1.0` — scaffold. The persona, agent, mode, and routing are written. Bundle
**wiring should be validated** before first real use:

- Run `validate-bundle-repo` (or consult `foundation:foundation-expert`) to
  confirm the `agents:`, `modes:`, and `tools:`/`tool-skills` keys in
  `occams-machete.md` resolve correctly in your foundation version.
- Or run it through **bundlewizard** (`/bundle-verify`) for a three-level audit.

## Lineage

Modeled after, and built to complete, the `cranky-old-sam` and
`crusty-old-engineer` skills. Same grumpy-craftsman DNA, sharper edge, and —
unlike its siblings — a willingness to actually pick up the tool.
