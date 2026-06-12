# Occam's Machete evaluation — project conclusion

## The arc
Code-reduction eval (the blade) → reframe (it's a **cognition-lens panel**, not a code tool)
→ pre-registered diagnostic study of the **anti-conflation guard** → Phase 1a found the guard
**one-sided** → the bundle diagnosed its own defect → Phase 2 **symmetric-guard fix** validated
in-sample → Phase 1b **generalization** on fresh held-out probes.

## What is established (robust)
1. **The blade reduces safely.** Only arm that never deletes load-bearing-but-untested code
   (composite 1.00 vs 0.83/0.79); recovered gap +0.167.
2. **The anti-conflation guard had a real, specific defect.** Phase 1a (n=20, frozen,
   voice-neutralized, blind judge, clean style-only negative control): the lens never
   pathologized a *reasoned* divergence (100%) but **affirmatively cleared 50% of unexplained
   smells** (vs a generic critic's 20%) — driven by the *reasoning profile, not voice*.
3. **The bundle can critique itself.** Asked to judge its own guard, `mj-reviewer` diagnosed
   the one-sidedness ("don't convict without proof ≠ acquit without proof") and prescribed the
   precise fix (aim at the *question*, not the flag; "reason" = citable incl. merits).
4. **The fix works and the reasoning generalizes.** Phase 2 (same probes): over-clearing
   50%→20%, mass into *question* not *flag*, protective half intact. Phase 1b (fresh probes):
   the fixed lens is the **best arm — 80% vs baseline 65%**, leading on the protective half
   (90% vs 70%); pipeline validated (calibration 100%).

## What is NOT established (the honest residual)
1. **Fidelity to MJ.** Everything so far scores the lens against *synthetic construct labels*
   or *itself*. "Reasons well / consistently" ≠ "reasons like MJ." **Only the human-MJ
   judgments close this** — the form is ready (`phase1b/MJ-FORM.md`); the lens-as-proxy is
   circular by construction.
2. **Statistical significance** on the primary (McNemar p=0.0625; the baseline ceiling, not a
   weak effect, ate the power).
3. **The over-clear fix's generalization** specifically — Phase 1b's fresh reason-absent probes
   were too unambiguous to reproduce the failure mode.

## Recommendations (to truly finish)
1. **Run the human-MJ gate** (~34 judgments, `MJ-FORM.md`). This is the single highest-value
   step and the only one that converts "the lens reasons well" into "the lens reasons like MJ."
2. **Author a fresh *ambiguous* reason-absent probe set** (defensible-but-undocumented smells)
   to actually re-test the over-clear fix out-of-sample.
3. **Power the primary**: ~35–40 reason-present probes where generic critics over-flag more.
4. **Ship the fix fully**: mirror the symmetric guard into `SKILL.md` + the blade (kept out of
   the measured run to isolate the variable).
5. **Extend to the other lens axes** (Sam / Brian / Crusty) as a pre-registered Holm family,
   reusing this harness.
6. **Enforce, don't advise**: make "never cut from red" a hook in the blade (the code-reduction
   eval showed the model can talk past prose — it edited a failing test to claim green).

## Bottom line
The evaluation *method* succeeded end-to-end: it found a real defect, drove a self-diagnosed
fix, and showed the fixed reasoning generalizes — with full provenance (3 freeze points, every
result effect-size + CI + exact test, a clean negative control). The bundle is **measurably
better than when we started.** The one thing no automation can supply — whether this panel
truly reproduces *MJ's* judgment — is teed up and waiting on MJ.
