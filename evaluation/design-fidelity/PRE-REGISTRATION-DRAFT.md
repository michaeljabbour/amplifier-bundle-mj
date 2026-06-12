# Design-cognition fidelity benchmark — PRE-REGISTRATION v2 (SIGNED OFF — MJ confirmed 2026-06-12)

**§10 decisions CONFIRMED as recommended:** 6 arms incl. HOLISTIC · N=12 + 4 duplicates (16 reads) ·
MJ does the 3-scenario A/B gold anchor · primary = Wilcoxon `MACHETE > NATIVE` (≥2-scenario margin) ·
grit = blast-radius ladder · domains = product/strategy + team/process-workflow.

**Status: DRAFT v2, revised per amplifier-research review (statistician + methodologist +
preregistration-reviewer). Nothing is built or run until frozen.** v1's 4 open questions and the
reviewers' must-fix items are resolved below; the few decisions still needing MJ are in §10.

This is the eval Phase 1 was *not*: it tests **design / judgment** cognition, not technical-defect
triage.

## 1. Question
On open-ended design problems, does the **occams-machete (MJ) lens** reproduce MJ's design judgment
**more than plain Amplifier, more than a strong generic-holistic reviewer, and more than the
single-concern sibling lenses?** "Better" = (primary) higher structured-call agreement with MJ;
(secondary) higher A/B preference. H1 is decided on the primary metric alone.

## 2. Arms (6) — same base model, only the lens/persona differs
| code | arm | role |
|------|-----|------|
| NATIVE | amplifier-native (neutral "review this design") | floor / control |
| COS | cranky-old-sam | single-concern: simplicity |
| COE | crusty-old-engineer | single-concern: cost/consequence |
| ROB | restless-old-brian | single-concern: realness/critical-path |
| **HOLISTIC** | **strong generic multi-concern reviewer, NOT built from MJ** | **the specificity control** |
| **MACHETE** | occams-machete (mj-reviewer) | the MJ lens under test |

*(HOLISTIC is the key addition from review: without it, "MACHETE beats the mono-concern siblings" is
confounded with "any holistic reviewer beats narrow ones." MACHETE > HOLISTIC is the clean
MJ-**specificity** test.)*

## 3. Scenarios — synthetic, 2×2 grid, N=12 (3/cell)
| | technical | non-technical |
|---|---|---|
| **deep** (big blast radius / hard to reverse) | architecture / system-design call | product / strategy call |
| **shallow** (cheap / reversible) | local code-or-tooling design call | team / process / workflow-design call |

- **N = 12** (3/cell) + **4 hidden duplicates, separated in sequence** = **16 MJ reads.** (N=8 only
  as a fallback "large-effect bet" — the omnibus is underpowered there.)
- Non-technical column is **product/strategy** (deep) + **team/process/workflow design** (shallow).
  **Deliberately excluded:** prose/copy-editing (it is MACHETE's literal specialty → confound) and
  hiring (too noisy/values-laden).
- **Genuinely contestable** situations (no obvious answer), authored fresh post-freeze, none from
  MJ's 305-session / 17-article corpus.
- **Blinding of authoring:** the scenario author does **not** see any arm system-prompt while
  authoring; after authoring, a post-hoc **concern-balance audit** ensures no single concern type
  (e.g. "too much here / cut it") dominates the grid; MJ does a blind realism check before freeze.

## 4. Reference standard — MJ, cold & blind (the workload)
Per scenario, before seeing any arm output, MJ records:
1. **grit** — *blast-radius / reversibility ladder* (orthogonal to direction):
   `0 none` (ship as-is) · `1 surface` (local, reversible) · `2 structural` (re-shape a module/section, bounded) · `3 foundational` (ripples across the system, hard to reverse). **Scored grit-exact.**
2. **direction** — ship-as-is / tweak / redesign / kill
3. **load-bearing concern** — the one factor that decides it (1 line)
4. **read** — 2–4 sentences of his actual reasoning

≈ 16 reads. Plus a small **A/B gold-anchor** pass (§6). **Intra-rater rule:** both members of each
duplicate pair must match on grit AND direction; a discrepancy → MJ re-reads that scenario blind;
persistent discrepancy → scenario flagged and reported.

## 5. Scoring — structured (primary) + A/B (secondary)
**Composite agreement** per scenario × arm = mean of three binary matches vs MJ:
`grit-exact` + `direction-exact` + `load-bearing-concern match` (grader judges semantic equivalence
to MJ's one-liner) → a score in {0, ⅓, ⅔, 1}. Design is **fully paired** (all 6 arms see every
scenario); **all inference is paired/within-scenario.** We never gate on absolute agreement rates or
Clopper–Pearson intervals (the Phase-1 trap: 8/8 at n=8 → CP lower 0.69 < 0.70).

## 6. Hypotheses, tests, and disconfirmation (frozen)
**PRIMARY (the one confirmatory gate):**
- **H1: MACHETE composite agreement > NATIVE**, one-sided **Wilcoxon signed-rank** on per-scenario
  composite differences (robustness: exact sign test). **Minimum meaningful difference: ≥ 2
  scenarios (≈17 pp at N=12).** **Disconfirmed if MACHETE ≤ NATIVE.**
- *Honest caveat (per review): H1 is expected to pass largely by construction (a lens built to embody
  MJ's philosophy should beat a neutral assistant). It confirms "the lens does work" — it is NOT the
  substantive fidelity test.*

**SECONDARY / EXPLORATORY-RIGOROUS (effect sizes + CIs; no pass/fail gate at this N):**
- **The substantive claim — MACHETE > HOLISTIC** (MJ-specificity, not just "holistic"). Reported as a
  Bradley–Terry strength gap + bootstrap CI. *Falsifier (qualitative): MACHETE ≤ HOLISTIC ⇒ the lens
  captures "holistic", not MJ.*
- **H2 (sharpened): MACHETE ≈ the best sibling on each sibling's *home* quadrant, but MACHETE > all
  siblings on the deep/contested cells where concerns conflict.** Reported as BT gaps per arm.
  *Falsifier: MACHETE ties everywhere and wins uniquely nowhere ⇒ no MJ-specificity.* A sibling
  matching MJ on its home quadrant is **validating** (it tells us MJ's call there is dominated by
  that concern), not a MACHETE failure.
- **A/B preference:** blind LLM comparison grader ranks the 6 arms' neutralized reads by alignment to
  MJ's neutralized read. **Bradley–Terry** on pairwise-decomposed rankings; arm strengths + CIs via
  **scenario-cluster bootstrap (B=2000)**; **Friedman + Kendall's W** omnibus on *consensus* ranks;
  Holm-adjusted post-hoc only if Friedman clears. **A/B is corroborating, not confirmatory; A/B alone
  is not evidence of fidelity.**

## 7. Analysis discipline (frozen)
- **One primary ⇒ no multiplicity correction on it.** Hierarchy: (1) primary H1; (2) secondary
  MACHETE-vs-HOLISTIC and H2 and A/B (reported with CIs, uncorrected, no gate); (3) exploratory:
  per-quadrant and per-dimension reads.
- **No quadrant-level inference** (n=3/cell) — quadrants are coverage + qualitative pattern only.
- **Grader trials are de-noising, not extra N:** aggregate ≥3 grader passes/models to ONE consensus
  per scenario *before* inference (avoids pseudoreplication). Report inter-grader reliability
  (Kendall's W / ICC) separately as a measurement-quality check.
- **Per-dimension agreement** (weighted κ for grit, κ for direction, match-rate for concern) is
  descriptive only — κ CIs are huge at this N.
- **Expansion rule (frozen):** expand 12→ (e.g. 20) **iff** H1 difference is a marginal 1–2 scenarios
  AND A/B is directionally positive. If H1 ≥ 3 scenarios + A/B positive → report positive, no
  expansion. If H1 ≤ 0 → negative, no expansion. Floor effect (all arms < 50%) → qualitative review,
  no expansion until resolved.

## 8. Blinding chain & validity (carried + hardened)
- **Three distinct model families:** scenario author ≠ voice-neutralizer ≠ grader. Author blind to
  arm prompts; neutralizer blind to arm identity; grader different family from both.
- **Voice-neutralize MJ's read + all 6 arm reads** with the same neutralizer; verify it strips
  *voice* without converging *judgment* (measure pre/post: voice signal drops, call signal doesn't).
- **A/B gold anchor:** MJ personally ranks alignment on a **3-scenario subset, run LAST**, blind to
  arm identity — purpose is to **validate the LLM grader as a proxy** (correlate LLM-ranks vs
  MJ-ranks), not to score MACHETE. Keeps MJ out of the main A/B loop (self-recognition bias).
- Non-mappable arm output → scored a miss on that sub-component. Floor/ceiling scenarios retained,
  flagged in results.

## 9. Limitations (stated up front)
- **H1 is circular by construction**; the substantive tests are MACHETE-vs-HOLISTIC and the
  deep/contested-cell wins. A positive H1 with MACHETE ≤ HOLISTIC means "opinionated persona >
  neutral," NOT "MACHETE tracks MJ."
- **Synthetic-only** scenarios bound the claim to synthetic design judgment (ecological-validity cost
  of the leakage guard).
- **N=12 is small / fuzzy:** one confirmatory primary + exploratory-rigorous rest. Not a powered
  multi-arm significance study.

## 10. Decisions still needing MJ (then we freeze + build)
1. **6 arms incl. HOLISTIC** — OK? (Adds an arm the harness runs; **no extra MJ reads**.)
2. **N=12 + 4 duplicates = 16 cold reads** — OK, or fall back to N=8 (weaker)?
3. **A/B gold anchor:** will you do the blind 3-scenario ranking pass (run last)? [rec: yes]
4. **Primary endpoint = Wilcoxon (MACHETE > NATIVE, ≥2-scenario margin)** — accept, or prefer the
   assumption-light "MACHETE ranked #1 in ≥ ⌈0.6N⌉ scenarios vs chance" binomial?
5. **Grit = blast-radius ladder** (§4) and **non-tech domains = product/strategy + process/workflow**
   — accept, or override?

## What gets frozen on sign-off
This doc, the 12 scenarios (authored + hashed), the 6 arm system-prompts, the neutralizer prompt, the
grader prompts + model families, and the analysis plan → git tag `design-fidelity-freeze`.
