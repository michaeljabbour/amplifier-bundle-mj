# Few-shot fidelity campaign — CHARTER / PRE-REGISTRATION v2 (validated; awaiting MJ sign-off)

**Status: SIGNED OFF by MJ 2026-07-08 (all 5 decisions confirmed: exemplars = his 12 reads
verbatim in the artifact; ~21 lock reads only if the dev gate clears; pre-committed artifact rule
accepted; honest MDE accepted; fine-tuning out of scope). Adversarially validated (5 defects
corrected — see ADOPTED AMENDMENTS at bottom, which SUPERSEDE conflicting text above). FROZEN.**

## Why this campaign
The hill-climb closed with a decisive result: on claude-fable-5, **prompt-wording mutation is an
exhausted lever** (6 firewalled variants, 2 rounds, 0 gate clears; all variants fail/succeed on the
same scenarios identically — the base model's judgment dominates). The remaining MJ-gap lives in
**genuinely contrarian calls** (e.g., killing outright what the model would merely question).
Instructions don't flip those; **examples might**. This campaign tests the next lever:
**few-shot exemplars of MJ's actual calls, in-context** (ICL).

**Fine-tuning is explicitly OUT OF SCOPE:** claude-fable-5 (the deployment model) exposes no
fine-tuning API; tuning a different base model would change two variables at once.

## The lever
Embed K worked exemplars into the lens: *(scenario → grit / direction / load-bearing concern /
2–4-sentence read)*, drawn **verbatim from MJ's 12 existing burned-scenario reads**. Those 12 are
burned for *evaluation* but are clean as *training material* — standard train/test hygiene. The
exemplars become part of the shipped artifact.

**MJ's new cost: one sitting of ~17 cold reads (the sealed lock set). Zero exemplar-authoring time.**

## Arms (all on claude-fable-5, the deployment model)
| arm | what it tests |
|---|---|
| CHAMPION (current lens, 0.556 baseline) | incumbent |
| **V3+K-SHOT** (lean platform + K MJ exemplars) | the chartered lever |
| **NATIVE+K-SHOT** (neutral reviewer + same exemplars) | does the persona text matter at all once exemplars exist? (the value-attribution control) |
| NATIVE (bare) | floor |

## Selection WITHOUT new labels or HARKing: leave-one-out on the burned 12
For each burned scenario s, build the few-shot prompt from exemplars drawn only from the *other 11*,
score on s. This yields an n=12 dev estimate per configuration with the test item never in its own
prompt. **The configuration space is pre-enumerated** (no hand-tuning on results):
K ∈ {4, 8, 11} × selection ∈ {random-seeded, quadrant-diverse} × format ∈ {compact, full-read}.
Best LOO configuration (highest mean composite; ties → smaller K) becomes THE challenger. One
challenger only.

## Confirmation — the sealed lock set (the only place claims come from)
- ~15 fresh scenarios + 2 hidden duplicates, authored by a **blind agent** (sees neither exemplars
  nor any MJ read), same 2×2 grid + concern-balance audit as before; **MJ reads cold, once,
  after freeze**; sealed.
- Decontamination (inverted from hill-climb): exemplars legitimately contain MJ text now; the rule
  is **lock scenarios must not overlap exemplar scenarios** (n-gram + semantic audit, blind author).
- **Primary (one test): challenger > CHAMPION**, paired Wilcoxon, one-sided α=0.025 (this campaign
  gets 2 lock openings max, Bonferroni — opening #2 reserved for one revision).
- **Attribution secondary:** challenger vs NATIVE+K-SHOT (paired, reported with CI, no gate) — if
  they tie, the fidelity lives in the exemplars, not the persona; that reshapes the bundle honestly.
- **Guards:** concern-match losses ≤ 2 (protect the lens's strength); escalation rate within the
  control band; A/A stability spot-check for the few-shot arm (long prompts could change sampling
  stability; 12×3 fresh resamples, F must stay < 0.08).
- MJ ceiling: the 2 duplicates re-measure self-consistency on the new set.

## Pre-committed outcomes (all first-class)
1. **Challenger clears** → adopt few-shot lens; re-validate on a second base model (standing rule).
2. **Challenger ties champion** → exemplars don't transfer beyond their own scenarios; MJ's
   contrarian calls are situation-specific; record and stop this lever.
3. **NATIVE+K-SHOT ≈ challenger (whenever measured)** → the persona prose is decorative once
   examples exist; the honest artifact is "12 worked examples + a thin frame."
4. LOO shows no configuration beats champion on dev → **do not collect MJ's lock reads at all**;
   campaign closes at zero MJ cost.

## Stop rules
(a) outcome 4 (no dev signal → stop before any MJ time); (b) both lock openings spent;
(c) any guard breach on the challenger → reject, one revision allowed (opening #2), then stop.

## Sequencing
1. Validate this charter (adversarial reasoning review) → MJ sign-off.
2. Build LOO harness; run the 12-config sweep (machine time only).
3. **Gate: only if a config beats champion on LOO dev** → blind-author lock set → MJ's one sitting.
4. Freeze challenger + lock → run confirmation → verdict.

---

## ADOPTED AMENDMENTS — adversarial validation review, 2026-07-08 (SUPERSEDES conflicting text above)

The review found 5 defects in the draft: (1) "best LOO config" is a max over ~10 correlated
estimates → winner's-curse optimism ≈ +0.08–0.13, so a bare "beats 0.556" dev gate is a coin-flip
generator — a **margin gate** is mandatory; (2) the A/A stability check must run **BEFORE** the
LOO sweep (the near-determinism claim was only ever measured on a short prompt; K=11 few-shot is a
different regime); (3) the config grid mis-counted (K=11 collapses selection → **10 unique
configs**); (4) outcome 3 as written was HARKing bait — the **artifact rule must be pre-committed**;
(5) same-generator exemplars can inflate the ICL effect (sibling-scenario lookup, label-marginal
shift, concern-copying) → **off-grid transfer stratum + leakage diagnostics** required.

### Corrected protocol (frozen on sign-off)

```
SELECTION (dev, machine-only — burned 12, LOO)
1. Configs: pre-enumerated, DEDUPLICATED (K=11 collapses selection) → 10 unique.
   Arms swept: V3+K-SHOT and NATIVE+K-SHOT (attribution measured at dev too).
2. A/A FIRST: longest config (K=11, full-read), 12×3 resamples, F<0.08.
   Breach → drop that cell family, re-A/A the longest survivor. No A/A pass → no sweep.
3. LOO: for each scenario, exemplars from the other 11 only; majority-of-3; same
   scorer as deployment. Report per-component (grit / direction / concern) breakdown.
4. DEV GATE (both required): (a) best-config LOO composite ≥ 0.667 (champion + 4/36,
   the winner's-curse margin); (b) paired per-scenario losses to champion ≤ 2.
   Ties within 1/36 → smaller K, then compact format. ONE challenger; its exact
   K/selection-seed/format frozen verbatim as the shipped-artifact spec.
5. Gate fails → outcome 4: campaign closes at ZERO MJ cost. No exceptions, no reruns.

LOCK SET (only if dev gate clears)
6. Blind author (sees no exemplars, no MJ reads): ~15 fresh on-grid scenarios with
   VARIED surface form/domain/length + 4–5 OFF-GRID transfer scenarios + 2 hidden
   duplicates. N-gram + semantic decontamination vs exemplar scenarios.
7. MJ reads cold, once, after freeze (~21 reads). Duplicates → self-consistency
   ceiling only; EXCLUDED from all inferential n.
8. Arms (identical output-format instructions; parse-failure rule pre-registered):
   CHAMPION | V3+K-SHOT (challenger) | NATIVE+K-SHOT | COS+K-SHOT | NATIVE bare.

CONFIRMATION
9. Primary (only gate): challenger > CHAMPION, paired exact Wilcoxon (Pratt zeros),
   one-sided α=0.025, on-grid n≈15. HONEST MDE stated up front: ≈ +0.17
   near-unidirectional; power for a mixed +0.10 is low → a miss is recorded as
   "underpowered," not "falsified." Point estimate + bootstrap CI reported regardless.
10. PRE-COMMITTED ARTIFACT RULE: if the primary clears AND NATIVE+K-SHOT ≥
    challenger − 1/45 → ship the SIMPLER artifact (thin frame + exemplars; persona
    prose retired). Decided now, not after seeing results.
11. Descriptive (no gates): challenger vs COS+K-SHOT and vs COS; off-grid stratum
    reported separately; leakage diagnostics = exemplar-similarity vs per-scenario
    gain correlation + label-marginal shift. Strong leakage signal → any adoption
    claim is scoped to "generator-sibling scenarios."
12. Guards: concern-match losses ≤ 2; escalation band; A/A on the frozen challenger
    (12×3, F<0.08) before lock scoring. 2 lock openings max (Bonferroni α=0.025);
    guard breach → one revision (opening #2), then stop.
```
