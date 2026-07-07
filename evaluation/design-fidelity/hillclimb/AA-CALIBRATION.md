# A/A Calibration — noise floor of the design-fidelity eval

**Purpose:** Tier-0 gate from `HILL-CLIMB-PLAN.md` — before spending any budget climbing, measure
how much the eval swings when NOTHING changes: score the SAME champion arm (MACHETE) twice, from
independent samples, judged identically. If that noise floor is not comfortably below the
pre-registered Tier-1b gate, the hill is not measurable at this sample size and any observed
"improvement" from a real challenger could just be noise.

**Run:** `harness/aa_calibration.py`, 2026-07-07, 46.9s wall-clock (fast — heavy caching + parallel
calls, well under the ~10-20 min estimate).

## Method

- **Arm under test:** MACHETE (the current champion lens), both campaign models.
- **Group A (reused, no new calls):** the existing frozen champion samples 0-2 —
  `runs/20260707_034211/raw.jsonl` (claude-fable-5) and `runs/20260612_135125/raw.jsonl`
  (claude-sonnet-4-5) — 12 scenarios × 3 samples each, `raw_text` reused verbatim.
- **Group B (fresh, 72 new calls):** samples 3, 4, 5 for the SAME arm, generated with the
  **exact same prompt assembly** as `phase2_run.py` (arms/MACHETE.md system prompt + `USER_TEMPLATE`
  + `COMMON_TASK`, `ARM_TEMPERATURE=0.7` for sonnet, temperature omitted automatically for fable by
  the shared `llm.py`), routed through the same content-addressed cache (the sample index makes
  these genuinely fresh cache keys, not hits against samples 0-2).
- **Judging — uniform gpt-4.1 for everything, both groups, both models:** the byte-identical
  extractor prompt and concern-match judge prompt from `phase2_analyze.py` (imported directly from
  that module so nothing was re-typed), just pointed at `gpt-4.1` instead of whatever
  `EXTRACTOR_MODEL`/`GRADER_MODEL` `config.py` currently has pinned for the production Phase-2 run.
- **Scoring:** per scenario × group × model, majority {grit, direction, concern} over the 3 samples
  → composite = mean(grit_exact, direction_exact, concern_match) ∈ {0, 1/3, 2/3, 1} vs MJ's frozen
  ground truth (12 scenarios, given in the task). Paired diff `d_s = composite_B − composite_A`.
  `F = p90(|d_s|)` over the 12 scenarios.

Full numbers: `harness/runs/aa_calibration/aa_results.json`. Fresh Group-B generations:
`harness/runs/aa_calibration/aa_raw.jsonl`.

## Gate under test

> Tier-1b (pre-registered): **net wins (W−L) ≥ 5 AND mean gain ≥ max(0.08, F)**

This calibration asks: if I ran that exact gate check on two identical draws of the *same* champion
(i.e. the null case, no real change), would it fire?

## Results

| Model (role) | mean composite A | mean composite B | mean diff (B−A) | mean \|diff\| | F = p90(\|diff\|) | wins / losses / ties | net wins |
|---|---|---|---|---|---|---|---|
| **claude-sonnet-4-5** (PRIMARY) | 0.4444 | 0.4167 | −0.0278 | **0.2500** | **0.3333** | 4 / 4 / 4 | 0 |
| claude-fable-5 (GUARD) | 0.5278 | 0.5556 | +0.0278 | 0.0278 | 0.0000 | 1 / 0 / 11 | 1 |

Per-scenario diff vectors (S01→S12, composite_B − composite_A):

- **sonnet:** `[0, 0, +0.333, −0.667, +0.333, 0, +0.333, 0, −0.333, −0.333, +0.333, −0.333]`
- **fable:** `[+0.333, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`

## Verdict per model

### claude-fable-5 (guard model) — **MEASURABLE**

F = 0.0 (11 of 12 scenarios tied exactly across independent re-samples; the one scenario that
moved, S01, moved because the concern-match judge flipped 0→1 on a wording nuance, not because
grit/direction changed). Mean |diff| = 0.028 is **35% of the 0.08 floor** and net wins under pure
noise = 1 (**20% of the 5 required**). Pure A/A noise comes nowhere near firing the gate on this
model. Gate margin stays at the pre-registered 0.08.

### claude-sonnet-4-5 (PRIMARY model) — **NOT RELIABLY MEASURABLE at n=3 samples**

This is the important finding, and it runs opposite to the plan's working assumption (which
expected fable-5 to be the noisy guard and sonnet the stable primary). Here, sonnet — the model
the whole campaign objective is defined on — is the noisy one:

- **8 of 12 scenarios (67%) flipped composite score just from re-sampling the identical arm.**
  Only 4 scenarios tied.
- The swings are not small: four scenarios moved by a full 1/3 of the composite scale in each
  direction (S03, S05, S07, S11 up; S04, S09, S10, S12 down), and one (S04) moved by a full **2/3**
  (0.667 → 0.0), driven entirely by grit/direction disagreement between the two independent
  samples on the same scenario, same arm, same model.
- These up-swings and down-swings happened to cancel (4 wins, 4 losses → net wins = 0), which
  *technically* fails the "net wins ≥ 5" leg of the gate on this particular draw — but that
  cancellation is coincidence, not evidence of stability. Re-draw and the sign of several of
  those four-vs-four scenarios could easily tip.
- **F = p90(|diff|) = 0.333 — a full third of the entire 0..1 composite range**, more than 4× the
  pre-registered 0.08 floor. Per the plan's own pre-committed stop rule: *"A/A floor ≥ gate →
  hill unmeasurable at this n — that itself is the finding."*

**Fraction of the gate pure noise already reaches (sonnet):** net-wins fraction = 0/5 = 0% (looks
safe only by coincidence); mean-diff fraction of the *floor* = −0.028/0.08 = −35% (also looks safe
only because the signed mean cancels — the honest number is F, and **F alone is 417% of the
pre-registered floor**).

**Measurability verdict: sonnet is NOT reliably measurable at n=3 samples/scenario.** F=0.333 is
well past "gate must rise modestly" territory — it consumes a third of the entire scoring range,
meaning a real challenger would need to beat noise-level swings on 4+ scenarios just to clear the
floor, and the current design (12 burned scenarios × 3 samples) cannot distinguish that from a
lucky/unlucky resample. **Recommendation: ABORT hill-climbing on sonnet at this sample size** —
either (a) raise samples per cell substantially (5-9+) before any Tier-1b screening on sonnet, or
(b) treat fable-5 (which IS measurable, F=0.0) as the primary signal-bearing model for this round
and sonnet as a non-inferiority guard only, inverting the plan's original role assignment, or
(c) accept a much higher gate on sonnet (mean gain ≥ F = 0.333, i.e. a candidate would need to win
essentially every scenario) if sonnet must remain PRIMARY.

## Why this differs from the plan's working assumption

`HILL-CLIMB-PLAN.md` pre-registered the expectation that the frontier model (sonnet) *compresses*
persona-lens effects (Run B: Friedman W=0.04 — arms hard to tell apart on sonnet), and treated
fable-5 as the noisy guard needing a non-inferiority check. This A/A run shows something adjacent
but distinct: it's not that *real differences between arms* compress on sonnet — it's that the
**judged composite score for the identical arm is itself unstable** run to run. Both are
consistent with "sonnet's design judgments are less crisp/more sample-variable than fable-5's,"
but they are different failure modes and this calibration is the first direct evidence of the
second one. This is a legitimate, pre-committed campaign outcome (STOP condition (b) in the
plan), not a bug in the harness.

## Bottom line

- **claude-fable-5:** hill IS measurable; noise floor F=0.0, gate stays at the pre-registered 0.08.
- **claude-sonnet-4-5 (PRIMARY):** hill is NOT reliably measurable at n=3; noise floor F=0.333
  (4× the pre-registered floor, consuming a third of the entire composite scale). Per the
  pre-committed stop rule, this is itself the finding — recommend pausing Tier-1a/1b climbing on
  sonnet until sample size increases or the primary/guard roles are reconsidered.
