# Round 2 — Tier-1b SCREEN use #2 (FINAL screen)

**Date:** 2026-07-07 · **Campaign:** design-fidelity hill-climb (mj-reviewer lens) ·
**Tier-1b uses spent:** 2 of 2 — **screen budget now EXHAUSTED** (per HILL-CLIMB-PLAN.md,
MAX 2 USES per campaign)

## Method

Repeat of round 1 with three NEW variants, using the **same runner, minimally adapted**
(`harness/round2_tier1b.py`, copied from `round1_tier1b.py` — diff is arm list + output
paths + cache-stage tags + campaign/round labels only; pipeline, prompts, gate constants,
champion source, and MJ reference are byte-identical and were verified so before running).

- **Arms:** 3 new challenger variants
  (`harness/arms_variants/{V4_DIRCAL,V5_STAGE,V6_MERGE}.md`): V4_DIRCAL = the V4 direction-
  calibration mutation (four-label verdict-weight-must-match-evidence-weight anchor,
  otherwise the round-1 base persona); V5_STAGE = the staging-instinct-applied-to-the-
  verdict mutation ("say BOTH sizes explicitly" section added); V6_MERGE = a merge of the
  V4 direction-calibration language and the V5 staging-verdict language into one persona.
- **Model:** claude-fable-5 only, PRIMARY per the amended protocol (ledger round-0
  `protocol_amendment`) — no temperature (llm.py drops it for fable models).
- **Scenarios:** the frozen 12 (`scenarios/scenarios_design.json`), identical prompt
  assembly to `phase2_run.py` (`USER_TEMPLATE` + `COMMON_TASK`, byte-identical to every
  other arm ever run in this campaign, including round 1).
- **Samples:** 3 per scenario per variant (indices 0, 1, 2). Cache keys are
  content-addressed over `(stage, model, scenario_id, arm, sample, prompt)` with
  `arm` = the new variant code (`V4_DIRCAL` / `V5_STAGE` / `V6_MERGE`), so none of these
  108 fresh calls collide with the champion's MACHETE cache entries, round 1's V1/V2/V3
  entries, or each other. 108 arm calls total (3 variants × 12 scenarios × 3 samples).
- **Extraction:** gpt-4.1, `phase2_analyze.EXTRACT_SYSTEM` / `EXTRACT_TEMPLATE` imported
  directly (byte-identical, not re-typed) — 108 calls.
- **Concern-match judge:** gpt-4.1, `phase2_analyze.CONCERN_SYSTEM` / `CONCERN_TEMPLATE`,
  same byte-identical import — 36 calls (1 per variant per scenario, on the majority
  concern).
- **Majority vote:** per (scenario, variant) over the 3 samples, using
  `phase2_analyze._mode` (returns `None` on a tie — no plurality winner).
  composite = mean(grit_exact, direction_exact, concern_match) ∈ {0, ⅓, ⅔, 1}.
- **Champion baseline (paired side):** the same FRESH champion composites already computed
  in the A/A calibration run — `harness/runs/aa_calibration/aa_results.json →
  results.fable.per_scenario[*].group_b` (claude-fable-5, samples 3, 4, 5). Reused as-is,
  **not regenerated** — identical reference to round 1, so round 1 and round 2 are directly
  comparable on the same champion baseline.
- **Scorer role:** this run sees the MJ reference labels (below) to compute grit-exact /
  direction-exact / concern-match. The optimizer (variant author) never saw
  (scenario, MJ label, output) triples per the plan's FIREWALL rule — that constraint is
  upstream of this script and out of scope for the scorer.

### MJ reference (ground truth, frozen, verified identical to round 1 and to the task)

| Scenario | Grit | Direction | Concern |
|---|---|---|---|
| S01 | 0 | kill | solution without a felt problem; duplication found by audit not by anyone living with it |
| S02 | 1 | kill | cheap in-stack (Postgres) options unexhausted vs a new datastore nobody can operate |
| S03 | 1 | ship-as-is | measured review-latency + rubber-stamp incidents met by a minimal reversible remedy |
| S04 | 0 | ship-as-is | proportionality — tested two-call-site helper for a 15-person internal dashboard |
| S05 | 1 | ship-as-is | incident-validated fix; idempotent; config-only and trivially reversible |
| S06 | 1 | tweak | the dead branch is no longer a viable rollback — 11 months unexercised |
| S07 | 2 | redesign | irreversible revenue-model bet with zero metering and zero willingness-to-pay evidence |
| S08 | 0 | kill | revenue concentration — the 8% are top revenue decile and cite it in renewals |
| S09 | 2 | redesign | 3-month irreversible nav rework justified only by qualitative evidence; cheaper testable alt exists |
| S10 | 0 | kill | no measured problem; the standup is where blockers surface |
| S11 | 1 | ship-as-is | measured pain met by a minimal reversible policy |
| S12 | 1 | tweak | cost-benefit — pinned index solves the only observed pain for near-zero ongoing cost |

### Pre-registered GATE (identical to round 1)

PASS requires **ALL** of:
- (a) net wins W−L ≥ 5 across the 12 scenarios (win = variant composite > champion composite on that scenario)
- (b) mean paired gain ≥ 0.08
- (c) concern-match losses ≤ 1 (scenarios where champion concern-matched and variant did not)

## Results — per-variant gate table

Champion baseline composite mean (fable-5, A/A group B, samples 3–5): **0.5556**
(same reference as round 1, unchanged; reused, not regenerated).

| Variant | Composite mean | Δ vs champion | Wins–Losses–Ties | Net wins | Mean gain | Concern losses | Grit-exact /12 | Direction-exact /12 | Concern-match /12 | Escalation ct. | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **V4_DIRCAL** | 0.5278 | −0.0278 | 4–4–4 | **0** | **−0.0278** | **2** | 7 | 4 | 8 | 4 | **FAIL** (all 3 sub-gates fail) |
| **V5_STAGE** | 0.5556 | 0.0000 | 1–1–10 | **0** | **0.0000** | **0** | 7 | 3 | 10 | 4 | **FAIL** (net-wins and mean-gain fail; concern-losses passes) |
| **V6_MERGE** | 0.5556 | ≈0.0000 | 3–4–5 | **−1** | **≈0.0000** | **1** | 7 | 4 | 9 | 4 | **FAIL** (net-wins and mean-gain fail; concern-losses passes) |

**No challenger clears the gate.** All three FAIL. Per HILL-CLIMB-PLAN.md ("At most one
challenger proceeds per campaign leg"), no variant proceeds to Tier 2 on this leg either.
**This was screen use #2 of 2 — the Tier-1b screen budget for this campaign is now
EXHAUSTED.** Combined with round 1 (also 0/3 clears), this is round 2 of the pre-committed
"3 rounds without a Tier-1b gate clear → hill is flat" stop condition (a) — but the screen
budget hits its own hard ceiling first (2 of 2 used), independent of the 3-round counter.

### Per-scenario paired diff vectors (variant composite − champion composite)

| Scenario | V4_DIRCAL | V5_STAGE | V6_MERGE |
|---|---|---|---|
| S01 | −0.333 | −0.333 | −0.333 |
| S02 | +0.000 | +0.000 | +0.000 |
| S03 | +0.333 | +0.333 | +0.333 |
| S04 | −0.333 | +0.000 | −0.333 |
| S05 | +0.333 | +0.000 | **+0.667** |
| S06 | −0.333 | +0.000 | −0.333 |
| S07 | +0.000 | +0.000 | +0.000 |
| S08 | +0.333 | +0.000 | +0.000 |
| S09 | +0.333 | +0.000 | +0.333 |
| S10 | +0.000 | +0.000 | +0.000 |
| S11 | +0.000 | +0.000 | −0.333 |
| S12 | **−0.667** | +0.000 | +0.000 |

Reading the vector: **S01 is lost by all three variants, by the identical −0.333 margin —
the same structural blind spot flagged in round 1 (all three round-1 variants also lost S01
by exactly −0.333).** This is now a 2-for-2 finding across 6 total variants and is no longer
attributable to any one mutation's wording; it looks like a base-model (claude-fable-5)
tendency, not a persona-prompt defect, and is not something round 3 mutation wording is
likely to fix. **S03 is won by all three variants**, again by the identical +0.333 margin —
the mirror finding to S01, and also present for V3_COSHYBRID in round 1 (S03 win there too),
suggesting this benchmark scenario (API versioning) is where fable-5 + any of these persona
variants beats the champion's escalation to grit 2, consistently. V5_STAGE is the flattest
of the three (1 win, 1 loss, 10 ties) — it changes almost nothing relative to the champion
on this benchmark; V4_DIRCAL and V6_MERGE both show more movement in both directions but net
out near zero or negative.

## Anomalies (checked, not glossed over)

**Extractor parse failures: 0 of 108. Majority-vote ties: 0 of 108.** Every one of the 108
fresh generations across all three variants produced a gpt-4.1-parseable
`{grit, direction, concern}` at the individual-sample level, AND every (scenario, variant)
cell had a clean 3-sample plurality on both grit and direction — no `_mode()` ties at all.
This is a cleaner run than round 1 (which had 2 majority-vote ties, both on V2_LEAN, on the
two heaviest scenarios S03/S07). Confirmed by direct grep over `round2_results.json` for any
`true` value on `grit_extract_fail` / `direction_extract_fail` / `grit_majority_tie` /
`direction_majority_tie`: zero matches across all 324 per-scenario-per-variant flag checks
(4 flags × 12 scenarios × 3 variants + it's also confirmed via the `majority_ties: 0` /
`extract_failures: 0` summary fields printed for every variant).

**V4_DIRCAL's single largest loss is S12 (−0.667), a concern-match + grit-exact double
loss.** Champion concern-matched S12 (pinned-index, cost-benefit) and V4_DIRCAL did not
(the direction-calibration mutation's majority answer proposed an ongoing curation process
for what MJ and the champion both call a one-time onboarding-doc gap) — this is also one of
V4_DIRCAL's 2 concern-match losses (the other is S04), which is what fails gate sub-condition
(c) for that variant specifically (2 > the 1-loss ceiling). V5_STAGE and V6_MERGE do not
share this failure on S12 (both tie the champion there).

**V6_MERGE's largest gain is S05 (+0.667)**, the only scenario across all 9 (3 variants ×
this round) where a variant wins big: the champion's S05 majority escalated to `tweak` and
lost a concern-match point (champion concern was about needing an empirically-set timeout
value; MJ's and V6_MERGE's were both about the retry/load-amplification mechanism), while
V6_MERGE's majority landed on ship-as-is with a concern that matched MJ's. This is the merged
variant's one clear positive result and is exactly cancelled out elsewhere (S04, S06, S11
losses) in its own diff vector — net near-zero.

**Escalation counts (majority grit > MJ grit) are 4/12 for all three variants** — lower than
round 1's V1/V2 (5/12 each) and equal to round 1's V3_COSHYBRID (4/12), and still comparable
to (not obviously better than) the champion. As in round 1, no per-variant escalation-rate
comparison against the champion was in the pre-registered gate, so this is descriptive only.

**All three round-2 variants land within a narrow composite band (0.5278–0.5556)** —
tighter than round 1's spread (0.4167–0.5556) — and none moves the needle against the
frozen champion baseline. The high floor noted in round 1 (8 of 12 scenarios tying at 0.000
for every variant there) recurs here in a slightly different but related shape: S02, S07,
S10 tie at 0.000 for every one of these three variants too, meaning across BOTH rounds (6
variants total) those 3 scenarios have never produced a single win or loss against the
champion — a persistent floor independent of which persona mutation is tried.

## Decision

**No variant proceeds.** All three FAIL the pre-registered Tier-1b gate on claude-fable-5,
paired against the same fresh champion baseline used in round 1. V5_STAGE and V6_MERGE both
clear sub-gate (c) alone (concern losses ≤ 1) but fail (a) and (b); V4_DIRCAL fails all
three sub-gates. Per the ledger's "a strategy is dead only after 2 failures clearing the A/A
floor" rule — which was defined for round-1 strategies — these are new strategies with 1
failure each on record; but this matters less now than it did after round 1, because **the
Tier-1b screen budget for this campaign is exhausted** (2 of 2 uses spent, 0 remain). No
further Tier-1b screens can be run on any future variant under this campaign's pre-committed
budget without a protocol amendment.

**Combined round 1 + round 2 read:** 6 challenger variants evaluated, 0 gate clears, champion
composite (0.5556) never beaten on aggregate by any variant across 2 independent rounds.
Two consistent structural findings recur identically across both rounds and all 6 variants:
(1) S01 is lost by every variant tried so far, by the same margin, regardless of persona
wording; (2) S02/S07/S10 (round 2) and S02/S05/S06/S09/S10 (round 1, differently) sit at a
scoring floor where champion and challenger are indistinguishable on this benchmark. This is
evidence the remaining lever, if any, is not further mj-reviewer persona wording on
claude-fable-5 at n=3 — it is either the benchmark's scenario set, the extractor/judge
resolution, or the base model itself.

## Outputs

- `harness/runs/round2_tier1b/round2_raw.jsonl` — 108 raw generations
- `harness/runs/round2_tier1b/round2_extractions.jsonl` — 108 gpt-4.1 extractions (audit trail)
- `harness/runs/round2_tier1b/round2_results.json` — all numbers, full per-scenario detail
- `hillclimb/LEDGER.jsonl` — 1 entry per variant + 1 round-decision entry (this round),
  noting the screen budget is now exhausted (2 of 2 uses spent)
