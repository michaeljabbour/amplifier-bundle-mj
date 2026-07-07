# Hill-climb plan — improving the MJ-lens without fooling ourselves

**Goal:** iteratively raise the mj-reviewer lens's design-fidelity to MJ (composite = grit-exact +
direction-exact + concern-match vs MJ's cold reads), using the frozen benchmark as the objective —
without Goodharting the 12 burned scenarios, without over-fitting one base model, and while spending
MJ's reads (the scarce resource) at most twice.

**Provenance:** drafted from the Phase-2 expert prescriptions (methodologist tune/lock firewall,
statistician power arithmetic, amplifier/foundation-expert mutation menu), then adversarially
validated by a reasoning review that corrected four defects: (1) min-over-models would climb on
fable-5 noise (W=0.04 — arms indistinguishable there); (2) a +0.10 gate at n=12 has a ~25–40%
campaign-level false-pass rate; (3) "beat COS's 0.694" is an absolute-proportion bar our own experts
prohibited; (4) the optimizer reading per-scenario MJ labels is an unguarded leak channel.

## The corrected protocol (frozen on adoption)

```
OBJECTIVE: composite agreement with MJ on claude-sonnet-4-5 (PRIMARY — where signal exists).
claude-fable-5 = paired NON-INFERIORITY GUARD only. All comparisons paired, same
scenarios/samples/judge. No absolute score bars anywhere.

TIER 0 — FREEZE (once, before round 1):
- Pin model snapshots; ONE judge/extractor (gpt-4.1) for ALL tiers of the campaign
  (spot-audited against MJ once); fixed sampling config.
- A/A CALIBRATION: champion vs champion (fresh samples), 12 scenarios × 2 models
  × 3 samples → noise floor F = p90 |paired composite diff|. If F ≥ gate margin,
  ABORT: the hill is unmeasurable at this n — that itself is the finding.
- Decontamination lint: no variant text may overlap burned-scenario content or
  MJ's phrasing (n-gram + semantic).
- FIREWALL: the optimizer (variant author) never sees (scenario, MJ label, output)
  triples. An auditor role reads misses and emits only coded failure-mode counts
  ("over-escalation ×8, concern-drift ×2"). NOTE: the root session is already
  partially contaminated (it has seen per-scenario tables); therefore ALL variant
  authoring is delegated to firewalled sub-agents receiving only coded counts.

TIER 1a — GRADIENT (cheap, no MJ, unlimited): ~40 fresh UNLABELED scenarios.
Label-free proxies vs NATIVE+COS run under identical conditions: escalation-rate
delta, concern-distribution divergence, verbosity. Calibrate the proxy once
against the burned-run diagnosis; climb here. K=3 variants/round from the
mutation menu; ledger every attempt with a strategy tag.

TIER 1b — SCREEN (burned 12, selection only, MAX 2 USES per campaign):
paired, champion re-run alongside. GATE (sonnet): net wins W−L ≥ 5 AND mean
gain ≥ max(0.08, F) AND concern-match losses ≤ 1. GUARD (fable): L−W ≤ 2.
At most one challenger proceeds per campaign leg.

TIER 2 — LOCK (MJ time): ~15 fresh scenarios + 2 hidden repeats (MJ ceiling),
MJ reads cold/blind BEFORE any variant exists; sealed. ≤ 2 openings ever,
one-sided α = 0.025 each (Bonferroni), paired Wilcoxon challenger > champion.
Guards: concern non-inferiority by win-count (losses ≤ 2); over-correction
guard (escalation rate within the control band). Each opening also runs COS +
NATIVE on the lock scenarios (API cost only) → success bar = paired
challenger ≥ COS on the lock, never any historical absolute number.

MUTATION MENU (round 1, from the expert review):
  V1 mvi-anchor    — minimum-viable-intervention anchor at the grit call
                     ("name the full concern; recommend the smallest reversible
                     first step") — preserves 'grit-3 problem, grit-1 first move'.
  V2 lean-4move    — 7 moves → 4 (foundations, adversarial, grit call w/ anchor,
                     verdict); drop the process-addition ("acceptance criteria")
                     language.
  V3 cos-hybrid    — radical lean-down toward the COS shape (one load-bearing
                     question + MJ's staging instinct); motivated by the lean
                     85-line COS/HOLISTIC prompts outscoring the 303-line lens.
  (do NOT touch: the anti-conflation guard — correct in interactive use.)

LEDGER: append-only (variant, strategy tag, tier, scores, decision). A strategy
is dead only after 2 failures clearing the A/A floor; one resurrection allowed
on a changed diagnosis.

STOP (pre-committed, each a first-class publishable outcome):
(a) 3 rounds without a Tier-1b gate clear → "hill is flat";
(b) A/A floor ≥ gate → "hill unmeasurable at this n";
(c) both lock openings spent.
Pre-registered honest prior: Run B showed persona effects COMPRESS on the
frontier model (W=0.04). "Persona-lens effects vanish with model strength;
repair unnecessary/undetectable at the frontier" is an expected and acceptable
conclusion, not a failure of the campaign.
```

## AMENDMENT — A/A calibration result (2026-07-07, run before round 1, as required)
Champion-vs-champion (fresh samples, 12 scenarios × 2 models × 3 samples, gpt-4.1 campaign judge):

| model | composite A | composite B | F = p90|paired diff| | verdict |
|---|---|---|---|---|
| claude-sonnet-4-5 | 0.444 | 0.417 | **0.333** | **NOT measurable at n=3** — 8/12 scenarios flipped on identical-arm resample; noise is 4× the gate floor |
| claude-fable-5 | 0.528 | 0.556 | **0.000** | **MEASURABLE** — 11/12 scenarios tied on resample; the 0.08 gate stands with huge headroom |

**Role swap (the calibration's own stop-rule fired for sonnet):** the validator assumed sonnet was
the stable signal source; the A/A shows the opposite — *the same arm's judged score bounces
run-to-run on sonnet*, while fable-5 is near-deterministic. Run B's arm compression (W=0.04) was a
finding about small TRUE differences; the A/A shows fable's *measurement noise* is ~zero, so even
small true gains can clear an honest 0.08 gate there.
**Amended roles: PRIMARY = claude-fable-5** (F=0.0; gate: net wins ≥5 AND mean gain ≥0.08 AND
concern losses ≤1). **sonnet-4-5 = descriptive check only** (report, no gate) unless samples/cell
are raised to ≥7 to stabilize its majority vote. Ledger round-0 entry records this.

## Sequencing
1. **Now:** A/A calibration (~72 cheap calls, zero MJ time) → is the hill measurable?
2. If measurable: author V1–V3 via firewalled sub-agents → Tier-1a proxy screen → Tier-1b use #1.
3. Only on a gate clear: ask MJ for the one-time lock-set reads (~17 cold reads) → Tier-2 opening #1.
4. Ship a new champion only on a confirmed lock win; then re-validate on both models (standing rule).

## MJ's total budget if everything goes right
One sitting of ~17 cold reads (the sealed lock set) — nothing else. All climbing is MJ-free.
