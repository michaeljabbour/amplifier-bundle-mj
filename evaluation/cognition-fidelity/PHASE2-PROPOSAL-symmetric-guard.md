# Phase-2 proposal — give the anti-conflation guard its symmetric half

**Status: PROPOSED, not applied.** The guard text is frozen for the Phase-1 study
(`tag cog-fidelity-phase1-freeze`). Applying this is a Phase-2 change: edit → new
freeze hash → re-run the same 40 frozen probes → then Phase 1b. Do NOT edit the
frozen artifacts mid-study.

## Why (evidence)
Phase 1a (3-way scoring, 40 held-out probes, voice-neutralized, blind judge):
- Reason-present (documented reason): lens **100%** avoid-defect (0/20 pathologized) vs baseline 75%. The protective half works — leave it alone.
- Reason-absent (no reason): lens **affirmatively cleared 10/20 (50%)** vs baseline 4/20 (20%), style-only 6/20 (30%). The negative control (style-only ≈ baseline ≠ lens) proves this is driven by the reasoning profile, not MJ's voice.

## Diagnosis (from the mj-reviewer lens, applied to its own guard)
The guard's text licenses exactly one move on an unexplained smell: *"downgrade it
to a **question**, not a verdict."* But **clearing is also a verdict** (a finding of
innocence). The guard prohibits the evidence-free *guilty* verdict and is silent on
the evidence-free *innocent* verdict — so "deliberate until proven otherwise"
(a presumption that means *don't convict without proof*) leaked into *acquit without
proof*. It is the **mirror image of the exact fallacy the guard exists to kill**:
"surface contradiction → confused" became "no stated reason → fine." Same
assuming-the-conclusion, opposite sign.

## The change (medium grit — refine existing text, don't rebuild)
Add one clause to `agents/mj-reviewer.md` move 3 (the anti-conflation guard), and
mirror it in the Output-shape summary and in `skills/occams-machete/SKILL.md` /
the blade:

> **Clearing is a verdict too.** Absent a citable reason — documented **or
> self-evident on the merits** — do not affirmatively clear an unexplained smell;
> **raise it as a question.** Flag only with citable evidence of *harm*; clear only
> with a citable reason it's *fine*; otherwise **suspend — the question is the
> honest default.** (This is the anti-conflation rule made symmetric: both
> verdicts now require citable evidence; only the question is free.)

Two design points the lens insisted on:
1. **Aim the new half at the QUESTION, not the flag.** If it nudges toward
   flagging, the lens just trades over-clearing for over-flagging and collapses
   into the generic baseline (16/20 flagged). The neutral default under genuine
   uncertainty is suspension.
2. **"Reason" = citable, documented OR evident on the merits.** An undocumented
   but engineering-defensible practice (e.g. client-side PCI tokenization) *has* a
   citable reason and may be cleared. Only smells with *no* reason of any kind get
   the question. Don't punish good-but-undocumented work.

## Acceptance test (re-run the SAME 40 frozen probes after the edit)
- **Must hold:** reason-present avoid-defect stays at **100%** (don't break the working half).
- **Target:** reason-absent **affirmative-clear** (`not_defect`) drops sharply; mass shifts into **question**, which becomes the plurality disposition.
- **Guardrail:** reason-absent **flag** does NOT balloon toward baseline's 16/20 — success is *question*, not *defect*.
- Then **Phase 1b**: human-MJ fresh judgments settle the merits-defensible cases (bug vs faithful) that synthetic labels cannot.

## Caveat on this proposal's provenance
This diagnosis came from the bundle's own `mj-reviewer` lens judging its own guard
(the user authorized "ask MJ as the bundle is activated"). It is a strong, coherent
**design input — not independent ground truth.** Using the lens to validate the lens
is circular; the human-MJ reference standard (Phase 1b) remains the arbiter,
especially for the merits cases.
