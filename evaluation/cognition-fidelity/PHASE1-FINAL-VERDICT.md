# Phase 1 — FINAL verdict (human-MJ reference standard)

MJ sat the 34-item blind exam. He is now the reference standard. This closes Phase 1.

## Reference-standard quality (must check first)
- **MJ self-consistency: 4/4 = 100%.** The 4 hidden duplicates were answered identically to
  their originals. The reference standard is rock-solid — fidelity ceiling is 100%, not capped
  by rater noise.
- **MJ vs the construct labels: 20/20 gold + 10/10 calibration = 100%.** MJ agreed with every
  pre-registered `expected_call` — including the three contested "question" items (Q07, Q16, Q19).
  This **retroactively validates the synthetic labels** used in Phases 1a/2/1B: they were
  MJ-faithful all along.

## The fidelity gate (the pre-registered co-primary)
Agreement with MJ on the 20 gold items:

| arm | agree w/ MJ | rate | Clopper–Pearson 95% lower |
|---|---|---|---|
| **lens (fixed)** | 16/20 | **80%** | **56.3%** |
| style-only | 15/20 | 75% | 50.9% |
| baseline | 13/20 | 65% | 40.8% |

**Pre-registered gate: lens CP lower bound > 0.70 → FAIL (lower = 56.3%).**

Per our own locked rule ("beats baseline but lower CI ≤ 0.70 ⇒ NEGATIVE, not spun"), this is a
**NEGATIVE result on the confirmatory fidelity claim.** Honest reading: the lens **agrees with MJ
80% of the time and leads every control** (style 75%, baseline 65%), but at **n=20 the confidence
interval is too wide** to assert >70% fidelity. This is *underpowered, not refuted* — at 80% true
agreement you need ~n=60–100 to clear the 0.70 bar. We pre-committed to calling this a negative,
and we are.

## What the 4 misses tell us (a real, new finding)
All four lens↔MJ disagreements run the **same direction — the lens is more aggressive than MJ:**

| Q | MJ | lens | what |
|---|---|---|---|
| Q07 | question | defect | single replica in prod — MJ raises it, lens condemns it |
| Q16 | question | defect | unbounded list response — MJ raises it, lens condemns it |
| Q19 | question | defect | `random.seed(42)` at import — MJ raises it, lens condemns it |
| Q09 | not_defect | defect | 100% rollout *with 3 weeks of shadow validation* — MJ clears it, lens condemns it |

- **Residual over-clears: ZERO.** The Phase-1a defect (over-clearing) is fully gone — MJ confirms
  the symmetric fix worked.
- **But the fix slightly OVER-corrected.** MJ uses **"question"** for genuine ambiguity; the fixed
  lens jumps to **"defect."** It also flagged a well-justified rollout (Q09) MJ cleared. The lens
  has the right instinct (don't clear unexamined smells) but **lacks MJ's calibration between
  "raise it" and "condemn it."** That's the next refinement — and it's the opposite of the
  original bug.

## The honest framing the user asked for
**This entire Phase 1 is a *technical-defect* evaluation, not a test of MJ's design cognition.**
Every one of the 34 items is a coding/config/API/schema correctness call — SQL injection, plaintext
passwords, money-as-FLOAT, TLS verification, force-push, PCI. It measures one narrow reasoning rule
(the anti-conflation guard) on *technical* artifacts. It does **not** touch what the bundle actually
exists to model: first-principles decomposition, the grit call (coarse/medium/fine), architectural
direction, "should this exist," the PM/logical-audit mindset — "the way MJ would do it." Even a
PASS here would certify *"faithful on technical-defect triage,"* never *"reasons like MJ on design."*

## Bottom line
- **Method: succeeded.** Found a real defect → bundle self-diagnosed → one-line fix → over-clearing
  eliminated (MJ-confirmed) → lens leads all controls against the human standard.
- **Confirmatory fidelity claim: NEGATIVE (underpowered).** 80% agreement, CI too wide at n=20.
- **New finding:** the fix over-corrected slightly toward flagging on ambiguous cases.
- **Scope caveat:** this is a technical-coding eval; the design/architecture/grit benchmark is the
  next, and more important, instrument.
