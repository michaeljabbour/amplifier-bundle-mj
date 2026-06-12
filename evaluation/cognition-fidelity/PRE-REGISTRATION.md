# Pre-registration — occam's-machete cognition-fidelity (Phase 1)

**Frozen:** 2026-06-11. Once committed + tagged, no edit to the profile, probes,
rubric, judge, or analysis plan is permitted without a new freeze hash and a new
study. This document is the commitment device that makes a "faithful" result
falsifiable.

Design owners: research:statistician (power), research:methodologist (bias
controls), research:research-coordinator (the four decisions). See conversation
record.

## Study type
Diagnostic-accuracy study. The **lens is the index test**, **MJ's real judgment
is the reference standard**, **fidelity = agreement** between them.
Frameworks: STARD (spine) + CONSORT (the paired arm) + construct validity.

## Phase 1 = the PRIMARY axis only, end-to-end
**Primary axis: the anti-conflation guard.** ("A divergence WITH a documented
reason must NOT be called a defect.") Chosen as the load-bearing, maximum-
separation, cleanly-binary facet — a generic strong critic over-flags reasoned
divergences by default, which is exactly what the guard forbids.

## Arms (independent variable = system prompt only; same model for all three)
- **lens** — the real `mj-reviewer` (mj-reviewer.md body + full mj-profile.md).
- **baseline** — same model + same task framing + same output shape, profile and
  anti-conflation/locality guards REMOVED. A generic sharp senior reviewer. (Fair
  baseline: only the profile is removed.)
- **style-only** (negative control) — MJ's voice/tics only (tone, cadence,
  coinages), WITHOUT the reasoning discipline. If style-only scores as well as the
  lens, the eval is measuring style not reasoning and is INVALID.

## Hypotheses
- **H1 (primary; McNemar exact, paired, n=20):** on probes containing a
  divergence-with-documented-reason, the lens withholds the "defect" label in
  agreement with the known-correct call MORE than the baseline. Discordant pairs
  favor the lens. Powered >0.95 for lens≈0.90 vs baseline≈0.40.
- **H1-fidelity-gate (co-primary; exact binomial, n=20 MJ-gold):** the lens's
  agreement with MJ's FRESH-PROSPECTIVE judgment has a Clopper–Pearson **lower
  bound > 0.70**.

## Minimum meaningful effect (BOTH must hold to claim "faithful")
1. lens − baseline accuracy ≥ **+25 percentage points** (absolute), McNemar p<0.05.
2. lens MJ-agreement Clopper–Pearson lower bound **> 0.70**.
**Explicit negative-result definition:** beats baseline but MJ-agreement lower CI
≤ 0.70 ⇒ NEGATIVE (recorded as such; not spun).

## Probe bank (construct-valid, HELD-OUT — none drawn from MJ's corpus)
- **Primary McNemar set:** 20 "reason-present" probes (a smell/divergence WITH a
  documented reason: commit msg / comment / doc). Correct call = WITHHOLD defect.
- **Construct-validity twins:** 20 "reason-absent/refuted" minimal-pair twins
  (same surface, reason removed). Correct call = FLAG. Reported separately:
  - lens **false-withhold rate** must be LOW (proves the lens is not a degenerate
    always-withholder).
  - **flip-rate** per arm across the 20 pairs (faithful reasoner flips; voice-mimic
    does not).
- **Construction controls:** facet-signaling vocabulary stripped; minimal-pair
  counterfactuals; ≥3 inverted-corpus memorization probes (surface resembles a
  plausible "known smell" but the correct answer is flipped).
- 3 LLM samples / probe / arm → **majority vote → 1 binary** (within-item noise
  controls ρ; samples used for self-consistency reporting, NEVER to inflate n).

## Judging pipeline (bias controls)
- **Voice-neutralization** of every arm output (separate model) BEFORE judging, so
  the judge cannot fingerprint MJ's style. Report raw AND neutralized.
- **Different-family judge:** arms = Claude; judge = OpenAI GPT (no self-preference).
- Judge is **blind to arm and to the hypothesis**; criterion is the neutral,
  facet-defined binary ("did the reviewer call the documented-reason divergence a
  defect? yes/no"). Never "which sounds more like MJ."
- Position/length controlled where applicable.

## MJ reference-standard protocol (Phase 1b — the confirmatory gate)
- **20 fresh-prospective** items on the anti-conflation guard, authored AFTER this
  freeze (not from corpus).
- **+4 intra-rater duplicates** (20%, shuffled, later) → MJ self-consistency ceiling
  (items MJ disagrees with himself on are discarded — no reference truth).
- **+~10 calibration items** to clear the judge gate BEFORE scoring.
- **AC1 gate:** Gwet's AC1 (judge vs MJ) ≥ **0.60** on the calibration set, else fix
  judge/rubric and do not score. (AC1, not κ, due to expected prevalence skew.)
- MJ answers **cold and blind** (never sees arm outputs first; voice-neutralized).
- ≈ **34 MJ judgments total**, primary axis only.

## Statistics & reporting
- Tests: **McNemar exact** (paired probes), **exact binomial / Clopper–Pearson**
  (preference, MJ-gold, agreement).
- Multiplicity: primary axis stands alone @ α=0.05 (Phase 1). The remaining ~5
  axes become one **Holm** family in Phase 2; Holm machinery validated on
  simulated data, not a second real axis.
- Report **two strata SEPARATELY** (never pooled): (A) constructed-probe accuracy,
  (B) MJ-gold agreement — plus their **concordance** (does A predict B?).
- Always report effect size + CI + exact p; never a bare p. Report MJ intra-rater
  ceiling (fidelity is capped by it). State power; a null at n=20 = "insufficient
  evidence," not "no effect."

## Sequence
Phase 1a (no MJ): build harness + probes, run lens/baseline/style-only against the
KNOWN-CORRECT labels, McNemar + style-only control. Proves the apparatus.
Phase 1b (MJ): calibration + AC1 gate + 20 fresh-prospective gold.
Phase 2: lock the proven harness; pre-register the remaining 5 axes as a Holm family.

## Frozen artifacts
See `FREEZE.json` (SHA-256 of profile + reviewer + skill + bundle, model ids for
both arms + judge + neutralizer, git commit SHA, corpus-manifest note).
