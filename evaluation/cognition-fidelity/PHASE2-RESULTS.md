# Phase 2 results — symmetric-guard fix (re-run of the 40 frozen probes)

Single-variable change (`agents/mj-reviewer.md` only, `tag cog-fidelity-phase2-freeze`,
8be67e9). Re-ran the SAME 40 frozen probes; lens arm re-generated with the fixed guard,
baseline/style-only served from cache (unchanged). 3-way re-judge.

## Lens — before (Phase 1a) → after (Phase 2)

| stratum / metric | Phase 1a | Phase 2 | acceptance |
|---|---|---|---|
| **reason-present** avoid-defect | 100% (0 wrong) | **100% (0 wrong)** | MUST-HOLD ✓ |
| **reason-absent** falsely-cleared (`not_defect`) | 10/20 (50%) | **4/20 (20%)** | TARGET: drop ✓ |
| **reason-absent** raised-as-question | 4/20 (20%) | **11/20 (55%)** | mass→question ✓ |
| **reason-absent** flagged (`defect`) | 6/20 | **5/20** | GUARDRAIL: no balloon ✓ |

Baselines (unchanged, cached): baseline false-clear 4/20 (20%), style-only 6/20 (30%).

## Verdict: the fix worked, exactly as the lens predicted
- Over-clearing collapsed from **50% → 20%** — now no worse than a generic critic, and the
  4 residual clears are plausibly the merit-defensible cases (for MJ to confirm in Phase 1b).
- The freed mass went into **question (20% → 55%, now the plurality)**, NOT into flagging
  (6 → 5). This is the precise, hard-to-hit target: the lens did **not** overcorrect into the
  over-flagging baseline (16/20). "The honest word is 'I have a question,' not 'ship it.'"
- The protective half was untouched: reason-present stayed **100%** (McNemar vs baseline
  unchanged: b=5, c=0, p=0.0625).

## Caveats (important)
- **This is a direction-of-change test, not generalization.** It re-runs the same 40 probes the
  fix was written against → necessary, not sufficient. Generalization requires FRESH probes and
  the human-MJ reference (Phase 1b). Do not over-read a perfect in-sample result.
- n=20 per stratum; same model (claude-sonnet-4-5) all arms; gpt-4.1 judge/neutralizer.
- The "4 residual clears" being correct (merit-defensible) vs wrong is exactly what human-MJ
  adjudicates — the fix did not, and cannot, settle that here.

## Status
- Phase-2 fix: **validated in-sample.** Committed + tagged. Mirror into `SKILL.md`/blade is a
  noted follow-on (kept out of this run to isolate the variable).
- Still pending the human: the ~34-item Phase-1b blind packet (`phase1b/MJ-FORM.md`) — sets true
  ground truth, adjudicates the residual clears, and tests generalization on fresh items.
