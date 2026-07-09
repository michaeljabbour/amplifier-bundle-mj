# Round 1 — Tier-1b SCREEN use #1

**Date:** 2026-07-07 · **Campaign:** design-fidelity hill-climb (mj-reviewer lens) ·
**Tier-1b uses spent:** 1 of 2 (per HILL-CLIMB-PLAN.md, MAX 2 USES per campaign)

## Method

Per the amended protocol (ledger round-0 `protocol_amendment`: the A/A calibration showed
claude-sonnet-4-5's judged score bounces run-to-run — F=0.333, 4x the gate floor, NOT
reliably measurable at n=3 — while claude-fable-5 is near-deterministic, F=0.000), this
screen runs **claude-fable-5 only**, PRIMARY per the amendment.

- **Arms:** 3 challenger variants of the mj-reviewer lens
  (`harness/arms_variants/{V1_MVI,V2_LEAN,V3_COSHYBRID}.md`), each authored per the
  HILL-CLIMB-PLAN.md mutation menu (V1 = minimum-viable-intervention anchor at the grit
  call; V2 = 7 moves lean'd to 4, process-addition language dropped; V3 = radical lean-down
  toward the COS shape — one load-bearing question + the staging instinct).
- **Model:** claude-fable-5, no temperature (llm.py drops it for fable models per its
  documented behavior).
- **Scenarios:** the frozen 12 (`scenarios/scenarios_design.json`), identical prompt
  assembly to `phase2_run.py` (`USER_TEMPLATE` + `COMMON_TASK`, byte-identical to every
  other arm ever run in this campaign).
- **Samples:** 3 per scenario per variant (indices 0, 1, 2). Cache keys are
  content-addressed over `(stage, model, scenario_id, arm, sample, prompt)` with
  `arm` = the variant code (`V1_MVI` / `V2_LEAN` / `V3_COSHYBRID`), so none of these 108
  fresh calls collide with the champion's MACHETE cache entries or each other.
  108 arm calls total (3 variants × 12 scenarios × 3 samples).
- **Extraction:** gpt-4.1, `phase2_analyze.EXTRACT_SYSTEM` / `EXTRACT_TEMPLATE` imported
  directly (byte-identical, not re-typed) — 108 calls.
- **Concern-match judge:** gpt-4.1, `phase2_analyze.CONCERN_SYSTEM` / `CONCERN_TEMPLATE`,
  same byte-identical import — 36 calls (1 per variant per scenario, on the majority
  concern).
- **Majority vote:** per (scenario, variant) over the 3 samples, using
  `phase2_analyze._mode` (returns `None` on a tie — no plurality winner).
  composite = mean(grit_exact, direction_exact, concern_match) ∈ {0, ⅓, ⅔, 1}.
- **Champion baseline (paired side):** the FRESH champion composites already computed in
  the A/A calibration run — `harness/runs/aa_calibration/aa_results.json →
  results.fable.per_scenario[*].group_b` (claude-fable-5, samples 3, 4, 5, generated with
  the exact same MACHETE system prompt / prompt assembly / judge as this screen).
  Reused as-is, **not regenerated** — this is the correct paired reference per the task
  brief and avoids spending a third fresh champion sample set.
- **Scorer role:** this run sees the MJ reference labels (below) to compute grit-exact /
  direction-exact / concern-match. The optimizer (variant author) never saw
  (scenario, MJ label, output) triples per the plan's FIREWALL rule — that constraint is
  upstream of this script and out of scope for the scorer.

### MJ reference (ground truth, frozen, verbatim from the task)

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

### Pre-registered GATE

PASS requires **ALL** of:
- (a) net wins W−L ≥ 5 across the 12 scenarios (win = variant composite > champion composite on that scenario)
- (b) mean paired gain ≥ 0.08
- (c) concern-match losses ≤ 1 (scenarios where champion concern-matched and variant did not)

## Results — per-variant gate table

Champion baseline composite mean (fable-5, A/A group B, samples 3–5): **0.5556**
(from `aa_results.json`, unchanged; reused, not regenerated).

| Variant | Composite mean | Δ vs champion | Wins–Losses–Ties | Net wins | Mean gain | Concern losses | Grit-exact /12 | Direction-exact /12 | Concern-match /12 | Escalation ct. | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **V1_MVI** | 0.4722 | −0.0833 | 0–3–9 | **−3** | **−0.0833** | **2** | 6 | 3 | 8 | 5 | **FAIL** (all 3 sub-gates fail) |
| **V2_LEAN** | 0.4167 | −0.1389 | 0–3–9 | **−3** | **−0.1389** | **2** | 5 | 2 | 8 | 5 | **FAIL** (all 3 sub-gates fail) |
| **V3_COSHYBRID** | 0.5556 | 0.0000 | 2–2–8 | **0** | **0.0000** | **0** | 7 | 4 | 9 | 4 | **FAIL** (net-wins and mean-gain fail; concern-losses passes) |

**No challenger clears the gate.** Per HILL-CLIMB-PLAN.md ("At most one challenger
proceeds per campaign leg"), **no variant proceeds to Tier 2** on this leg. This is
round 1 of the pre-committed "3 rounds without a Tier-1b gate clear → hill is flat" stop
condition (a) — 2 rounds remain before that stop condition would fire on its own terms.

### Per-scenario paired diff vectors (variant composite − champion composite)

| Scenario | V1_MVI | V2_LEAN | V3_COSHYBRID |
|---|---|---|---|
| S01 | −0.333 | −0.333 | −0.333 |
| S02 | +0.000 | +0.000 | +0.000 |
| S03 | +0.000 | +0.000 | **+0.333** |
| S04 | −0.333 | +0.000 | +0.000 |
| S05 | +0.000 | +0.000 | +0.000 |
| S06 | +0.000 | +0.000 | +0.000 |
| S07 | +0.000 | **−1.000** | +0.000 |
| S08 | −0.333 | −0.333 | **+0.333** |
| S09 | +0.000 | +0.000 | +0.000 |
| S10 | +0.000 | +0.000 | +0.000 |
| S11 | +0.000 | +0.000 | −0.333 |
| S12 | +0.000 | +0.000 | +0.000 |

Reading the vector: **8 of 12 scenarios tie at 0.000 for every variant** — the frozen
benchmark's floor for this base model and this composite metric is high (champion mean
0.556), leaving little room to move on scenarios where champion, MJ and variant all
already line up. All three variants lose S01 (audit-found duplication, no felt pain) by
the same margin. V2_LEAN's one catastrophic loss (S07, −1.0) is the dominant term in its
mean; V3_COSHYBRID is the only variant with any wins (S03, S08) but they're offset by an
S01/S11 loss, netting to zero.

## Anomalies (checked, not glossed over)

**Extractor parse failures: 0 of 108.** Every one of the 108 fresh generations produced
a gpt-4.1-parseable `{grit, direction, concern}` at the individual-sample level — no
arm silently failed to emit the terminal `GRIT:/DIRECTION:/CONCERN:/READ:` block in a way
the extractor couldn't read.

**But: 2 majority-vote ties, both on V2_LEAN, not extraction failures.** This is worth
stating precisely because the two look identical from the composite score alone:

- **S03 (V2_LEAN):** the 3 samples' extracted grit was `[2, 3, 1]` — three different
  values, no plurality, so `_mode()` correctly returns `None` → grit_exact=0 for that
  scenario. This is genuine **within-variant sample disagreement** on how heavy the API
  versioning call is (V2_LEAN's 3 fable-5 samples independently judged the same scenario
  as a bounded reshape, a foundational rework, and a local tweak), not a formatting bug.
- **S07 (V2_LEAN):** direction across the 3 samples was `[kill, tweak, redesign]` — again
  three different values, no plurality → direction_exact=0. Grit also disagreed (`[3, 1,
  3]`, no true tie there but the mode still landed on 3, escalating past MJ's 2). This is
  V2_LEAN's single worst scenario (diff = −1.0): champion composite there was a clean 1.0
  (MJ, champion, and — per the underlying raw text — even 2 of 3 V2_LEAN samples
  substantively agreed with MJ's redesign/kill call and the metering-evidence concern),
  but the 3-way split on direction with no majority zeroed out both exactness terms, and
  the *majority* concern ("no metering infrastructure means the proposal cannot be
  implemented") did not semantically match MJ's ("irreversible revenue-model bet with
  zero metering and zero willingness-to-pay evidence") per the gpt-4.1 judge, driving
  concern_match to 0 too. Net: a real signal (V2_LEAN is less consistent sample-to-sample
  on the two heaviest scenarios, S03 and S07 — both "deep" scenarios) got amplified by the
  majority-vote scoring rule into the single largest per-scenario loss in this screen.
  This is an honest property of the n=3 majority-vote design (also documented in
  AA-CALIBRATION.md as a real risk), not a defect in this script.

This distinction is recorded per-scenario in `round1_results.json` as
`grit_extract_fail` / `direction_extract_fail` (true per-sample extraction failure — 0
across the board) vs. `grit_majority_tie` / `direction_majority_tie` (all-samples-parsed,
no-plurality — 2, both V2_LEAN, both above). An earlier pass of this script conflated the
two under a single `parse_fail` flag; that was corrected before this writeup (see
`round1_tier1b.py` — the field no longer exists, replaced with the four booleans above)
so the anomaly is reported accurately.

**Escalation counts (majority grit > MJ grit) are high across all three variants — 5, 5,
and 4 of 12 — and comparable to (not obviously better or worse than) the champion.** No
per-variant escalation-rate comparison against the champion was in the pre-registered
gate, so this is descriptive only; flagged here because it's the kind of number a later
round's diagnosis should look at (over-escalation was named as a coded failure mode in the
plan's FIREWALL section).

**All three variants lose S01 by the same −0.333 margin.** This scenario (shared
notification platform, audit-found duplication, no team complaint) appears to be a
structural blind spot shared by V1/V2/V3 and the base fable-5 model, not something any one
variant's wording fixes — worth a note for whoever authors round 2's mutation menu.

## Decision

**No variant proceeds.** All three FAIL the pre-registered Tier-1b gate on claude-fable-5,
paired against the fresh champion baseline. V3_COSHYBRID is the closest (composite tied
with champion, net wins 0, concern losses 0 — it clears sub-gate (c) alone) but does not
clear (a) or (b). Per the ledger's "a strategy is dead only after 2 failures clearing the
A/A floor" rule, none of V1/V2/V3 is dead yet — each has 1 failure on record here (2 would
retire it, absent a changed diagnosis).

## Outputs

- `harness/runs/round1_tier1b/round1_raw.jsonl` — 108 raw generations
- `harness/runs/round1_tier1b/round1_extractions.jsonl` — 108 gpt-4.1 extractions (audit trail)
- `harness/runs/round1_tier1b/round1_results.json` — all numbers, full per-scenario detail
- `hillclimb/LEDGER.jsonl` — 1 entry per variant + 1 round-decision entry (this round)
