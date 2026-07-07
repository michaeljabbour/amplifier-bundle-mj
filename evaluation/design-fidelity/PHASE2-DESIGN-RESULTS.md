# Design-Fidelity Phase 2 — Results

**Run:** `harness/runs/20260612_135125` · 216 records (12 scenarios × 6 arms × 3 samples)
**Arms:** NATIVE, COS, COE, ROB, HOLISTIC, MACHETE (all `claude-sonnet-4-5`; only the system prompt differs)
**Extractor / concern-judge / neutralizer:** `gpt-4.1` (different family from the arms)
**A/B ranker:** `claude-sonnet-4-5` (different family from the gpt-4.1 neutralizer)
**Ground truth:** MJ's 12 reconciled reads (`MJ-DESIGN-FORM.md`)

> **Bottom line, stated plainly:** The pre-registered primary hypothesis — that MACHETE's
> composite agreement with MJ exceeds NATIVE's — is **not supported**. MACHETE scored the
> **lowest** composite of all six arms (0.444), losing to NATIVE on a net of 3 scenarios
> (one-sided Wilcoxon p = 0.84, sign-test p = 0.91). On the specificity test it also trails
> HOLISTIC (Δ = −0.167). The blind A/B ranker independently ranked MACHETE **last of six**.
> This is a negative result for the MACHETE arm on this frozen eval. Details and the (real,
> arm-neutral) measurement caveats are below.

---

## 0. Parse-bias correction (why we re-extracted)

The Stage-1 `raw.jsonl` carries a regex pre-parse that is **biased against MACHETE**: it failed
on **12 of 12 MACHETE records** (every MACHETE sample) and **0 of the other 180** records,
because MACHETE wraps its GRIT/DIRECTION block in markdown/qualified formatting the regex
doesn't recover. Scoring off that pre-parse would have silently zeroed MACHETE.

Per the instructions, we **ignored the pre-parse entirely** and re-extracted `{grit, direction,
concern}` **uniformly for all 216 records** with a single gpt-4.1 extractor under identical
rules (cached by content hash). Uniform re-extraction **failed on 0 / 216** records — including
all 12 MACHETE records the regex missed. So MACHETE's low score is **not** a parsing artifact;
it survives the bias correction.

---

## 1. Primary endpoint (frozen): MACHETE composite > NATIVE

Paired over the 12 scenarios.

| quantity | value |
|---|---|
| MACHETE mean composite | **0.444** |
| NATIVE mean composite | **0.556** |
| mean paired diff (M − N) | **−0.111** |
| 95% bootstrap CI (B=2000, resample scenarios) | **[−0.278, +0.056]** |
| scenarios MACHETE > NATIVE | **3** |
| scenarios NATIVE > MACHETE | **6** |
| ties | **3** |
| **net scenario margin (M − N wins)** | **−3** |
| meets pre-registered ≥2-scenario margin? | **No** (margin is negative) |
| one-sided Wilcoxon signed-rank (M > N) | **p = 0.844** |
| exact sign test (M > N) | **p = 0.910** |

**Verdict:** Fail to reject the null. MACHETE does not beat NATIVE; the point estimate runs the
*wrong* way and NATIVE wins ~2:1 among non-tied scenarios. The bootstrap CI straddles zero but is
centered below it. There is no evidence of a MACHETE advantage over the bare baseline.

---

## 2. Specificity: MACHETE vs HOLISTIC

The real MJ-specificity test — does the full MACHETE lens beat a generic "holistic reviewer" prompt?

| quantity | value |
|---|---|
| MACHETE mean composite | 0.444 |
| HOLISTIC mean composite | 0.611 |
| mean paired diff (M − H) | **−0.167** |
| scenarios MACHETE > HOLISTIC | 2 |
| scenarios HOLISTIC > MACHETE | 6 |
| ties | 4 |
| one-sided sign test (M > H) | p = 0.965 |
| one-sided Wilcoxon (M > H) | p = 1.000 |

**Verdict:** MACHETE is *less* aligned with MJ than the lightweight HOLISTIC prompt. The
specificity test fails in the negative direction.

---

## 3. Per-arm composite + per-dimension breakdown (mean over 12 scenarios)

| arm | composite | grit-exact | direction-exact | concern-match |
|---|---|---|---|---|
| ROB | **0.639** | 0.417 | **0.583** | 0.917 |
| HOLISTIC | 0.611 | 0.583 | 0.333 | 0.917 |
| NATIVE | 0.556 | 0.500 | 0.333 | 0.833 |
| COS | 0.556 | **0.667** | 0.333 | 0.667 |
| COE | 0.472 | 0.417 | 0.333 | 0.667 |
| **MACHETE** | **0.444** | **0.250** | 0.333 | 0.750 |

Observations (honest, not flattering to MACHETE):

- **ROB wins overall**, driven by the only above-baseline **direction-exact** rate (0.583) and
  top concern-match (0.917).
- **MACHETE has the worst grit-exact rate (0.250).** Inspecting the cells, MACHETE
  **systematically over-escalates blast-radius**: where MJ calls grit 1, MACHETE repeatedly
  returns grit 2 (S05, S06, S11), and it softens MJ's "ship-as-is" into "tweak/redesign". This is
  the *opposite* of the minimalist disposition the "Occam's machete" persona intends, and it is
  the main driver of its low composite.
- **Direction-exact is 0.333 for five of six arms** — uniformly low (see the label-semantics
  caveat in §6); ROB is the lone exception. MACHETE is not penalized more than its peers here.
- MACHETE's concern-match (0.750) is mid-pack — it often names a *reasonable* load-bearing factor
  even when its grit/direction call diverges from MJ.

---

## 4. A/B ranking (blind, neutralized, claude ranker)

MJ's 12 reads were voice-neutralized with the same gpt-4.1 neutralizer used on the arm reads.
For each scenario, a blind claude ranker read MJ's neutralized read + the 6 arms' neutralized
reviews and ranked the 6 by alignment to MJ. **3 order-randomized trials per scenario**, aggregated
to a consensus mean-rank per scenario *before* inference (de-noise first). All 36 trials parsed
cleanly (every scenario's six ranks sum to 21).

| arm | mean rank (1 = best aligned) |
|---|---|
| HOLISTIC | **2.86** |
| ROB | 3.14 |
| NATIVE | 3.47 |
| COS | 3.61 |
| COE | 3.81 |
| **MACHETE** | **4.11** |

- **MACHETE ranks 6th of 6** — least aligned to MJ in the holistic blind read, consistent with the
  structured composite.
- **Friedman χ² test: p = 0.363** → the rank differences across arms are **not statistically
  significant**.
- **Kendall's W = 0.091** → very weak concordance; the ranker sees little stable separation among
  the arms. Treat the A/B ranking as corroborating, not confirmatory — but note it corroborates
  *against* MACHETE, not for it.

---

## 5. Per-quadrant pattern (descriptive only, n = 3 each)

Quadrants read from `scenarios_design.json` (depth × domain). Composite means:

| quadrant | scenarios | NATIVE | COS | COE | ROB | HOLISTIC | MACHETE |
|---|---|---|---|---|---|---|---|
| deep / technical | S01–S03 | 0.44 | 0.56 | 0.33 | **0.67** | 0.56 | 0.33 |
| shallow / technical | S04–S06 | 0.56 | 0.67 | 0.44 | **1.00** | 0.67 | 0.33 |
| deep / non-technical | S07–S09 | 0.56 | 0.44 | 0.56 | 0.44 | 0.44 | 0.44 |
| shallow / non-technical | S10–S12 | 0.67 | 0.56 | 0.56 | 0.44 | **0.78** | 0.67 |

With n=3 per cell these are anecdotes, not estimates. The only consistent signal: **MACHETE is
weakest in the technical quadrants** (0.33 / 0.33), exactly where its grit over-escalation bites
(S05 retry config, S06 dead flag — both small reversible changes MJ rates grit 1, MACHETE inflates
to grit 2 / "kill"). MACHETE is most competitive in shallow/non-technical (0.67), tied with NATIVE.

---

## 6. Caveats and known ambiguities (read before citing any number)

1. **Direction-label semantics on remove/sunset proposals are genuinely ambiguous.** For
   scenarios where the *proposal is to remove something* (S08 sunset Reports, S10 replace
   standup), MJ labeled direction **"kill"** meaning *kill the proposal* (i.e., keep the existing
   thing). Several arms labeled the identical substantive conclusion **"ship-as-is"** (meaning
   *keep the current system as-is*). These are **semantically the same decision** under opposite
   labels, and the strict direction-exact metric scores them as misses. This depresses
   direction-exact roughly **equally across all arms** (five arms sit at 0.333) and therefore does
   **not** explain MACHETE's deficit — but it does mean the absolute direction-exact rates are
   pessimistic for everyone. A label rubric that scores "the recommended end-state" rather than
   the "kill/ship" token would lift all arms.

2. **MACHETE's deficit is concentrated in grit, not direction or concern.** Its over-escalation of
   blast-radius (grit-exact 0.250) is the dominant cause. This is a real, interpretable behavioral
   pattern, not a measurement artifact — it reproduces across both technical quadrants and survives
   uniform re-extraction.

3. **Power is low.** n=12 paired scenarios, 3 samples each; the A/B ranker shows weak concordance
   (W=0.09) and Friedman is non-significant. We can say MACHETE shows **no advantage** and a
   **negative point estimate**; we cannot precisely bound the size of any true effect.

4. **The extractor/judge is an LLM.** grit/direction were re-extracted and concern-match was judged
   by gpt-4.1. This is uniform across arms (no per-arm bias), but the absolute composite levels
   inherit the extractor's interpretation of the rules.

---

## 7. MJ self-consistency (intra-rater reliability)

The blind form embedded **4 hidden duplicates** (S02, S05, S08, S11). Per the task,
MJ's self-consistency on those duplicates was **4/4 on grit AND 4/4 on direction** — stated, not
recomputed here. The ground truth is internally consistent; the divergences reported above are
arm-vs-MJ, not MJ-vs-MJ noise.

---

## 8. Reproduce

```bash
cd evaluation/design-fidelity/harness
../../cognition-fidelity/harness/.venv/bin/python phase2_analyze.py
# writes runs/20260612_135125/phase2_results.json (+ phase2_extractions.jsonl)
# and ../PHASE2-DESIGN-RESULTS.md
```

All model calls are content-addressed cached (key includes `raw_text`), so re-runs are free and
deterministic against the frozen run dir.

---

## Expert review + DECISION (consulted 4 experts; do NOT change the lens yet)
amplifier-expert, foundation-expert, research methodologist, research statistician — strong convergence.

**1. Record the PRIMARY negative — it's confirmatory and earned.** As a one-shot design judge, MACHETE does not beat NATIVE (one-sided Wilcoxon p=0.84, point estimate −0.11) and ranks last of 6 on the blind A/B — last on two procedurally independent metrics. Statistician: ~80–85% posterior that MACHETE is *no better*; we "decisively reject superiority," cannot *certify* inferiority (CI crosses 0), and magnitude is unresolved at n=12.

**2. The grit-over-escalation "defect" is EXPLORATORY — don't act on it.** It is a post-primary (HARKed) hypothesis read off the same 12 points. Paired McNemar on grit-exact (run now): MACHETE loses the discordant count to NATIVE 4–1 (p=0.375), HOLISTIC 5–1 (p=0.219), COS 5–2 (p=0.453); ties ROB 4–4. Direction consistent in 3/4 comparators, **none significant.** A strong lead, not a confirmed effect (Friedman p=0.36, Kendall's W=0.09 corroborate).

**3. Three threats to acting now (methodologist, GRADE: 3 downgrades on the derived claim):**
- **HARKing** — derived after the primary failed.
- **Indirectness** — tested as a one-shot judge, not the lens's natural *interactive* use; "fixing" it risks Goodharting the wrong target.
- **Construct risk** — MJ rated the grit of his *recommended (staged-down)* change; the lens may rate the *raw* change → "over-escalation" could be a rubric artifact, not a fidelity gap.

**4. GATE before any change (cheap, on the existing 12):** resolve the grit-referent question first — code what each arm's grit refers to, and have MJ re-score ~4 disputed scenarios under the explicit instruction "rate the grit of the change THE LENS recommends." If MJ then agrees → **artifact → fix the rubric and re-run, do NOT touch the lens.** If MJ still says it escalated → real gap → proceed.

**5. IF real, the fix is known and principled (amplifier-expert + foundation-expert converge):** the bug is a *missing mechanism*, not a wrong policy. Add a **minimum-viable-intervention anchor at the grit call**: name the full concern, then recommend the *smallest reversible first step* ("concern is X; minimum viable move is Y; start with Y"). This preserves "grit-3 problem, grit-1 first move" and does NOT hardcode low grit. Also: the mj-reviewer prompt is over-elaborate (303 lines / 7 moves) vs HOLISTIC (85 lines, which beat it) — lean 7→4 moves and drop the "acceptance criteria" language (it prompts process-addition). **Do NOT touch the anti-conflation guard** (correct in interactive use).

**6. Validate INTERACTIVELY + on FRESH data — never on these 12:** 4–6 real interactive sessions (check the opening frame — does MJ have to say "too heavy, start with X"?), then a fresh hold-out: ~30 new scenarios, tune on 15 / lock 15–20 (touched once), pre-registered, grit-exact primary via paired McNemar (N≈30 powers a realistic 0.25→0.50; non-inferiority guard: concern-match stays ≥0.70; over-correction guard on scenarios where heavy escalation is correct).

**DECISION:** record the confirmatory negative; **do NOT change the lens.** Next step is the cheap grit-referent gate (needs MJ to re-score ~4 scenarios) — it may dissolve the finding into a measurement artifact before any lens change is on the table.

---

## MODEL RE-RUN (2026-07-07) — Fable 5 arms / GPT-5.5 judge · run `20260707_034211`

Per MJ: re-run the frozen benchmark with **claude-fable-5** as the arm model (was
claude-sonnet-4-5) and **gpt-5.5** as the different-family neutralizer/extractor/grader (was
gpt-4.1). A/B ranker follows ARM_MODEL (claude-fable-5). Same 12 frozen scenarios, same 6 frozen
arm prompts, same MJ reference reads (model-independent). Manifest: `FREEZE-rerun-fable5.json`.
216/216 records, 0 API errors; uniform LLM re-extraction as before.

### Results (vs the original sonnet run)

| metric | sonnet/gpt-4.1 (Jun 12) | **fable-5/gpt-5.5 (Jul 7)** |
|---|---|---|
| MACHETE composite | 0.444 — **last of 6** | **0.583 — tied 2nd** (with NATIVE) |
| best arm | ROB 0.639 | **COS 0.694** |
| PRIMARY MACHETE−NATIVE | −0.111, p=0.84 | **0.000, p=0.625** (net margin +1) — still NOT supported |
| MACHETE vs HOLISTIC | −0.167 | **+0.028** |
| blind A/B mean rank | 4.11 — 6th/6 | **3.25 — 2nd/6** (NATIVE 3.08 best) |
| grit-exact (MACHETE) | 3/12, escalation 8/12 | **6/12, escalation 5/12** (= NATIVE/COE) |
| Kendall's W (A/B) | 0.091 | 0.044 (Friedman p=0.76) |

Full composite (fable-5): COS 0.694 · NATIVE 0.583 · MACHETE 0.583 · HOLISTIC 0.556 · ROB 0.528 · COE 0.500.

### Honest interpretation
1. **The pre-registered primary still fails** — MACHETE does not beat NATIVE (exact tie). Under
   BOTH model configurations, "the MJ-lens adds measurable design-fidelity over plain Amplifier"
   is unsupported.
2. **The "MACHETE is worst" finding did NOT replicate.** Last-of-6 was a *sonnet-specific* result:
   under Fable 5 MACHETE is tied-2nd on composite, 2nd on blind A/B, and edges HOLISTIC. The
   headline negative was model-dependent, not a stable property of the lens.
3. **The grit-over-escalation driver largely dissolved** (3/12 → 6/12 grit-exact; escalation
   8/12 → 5/12, now equal to NATIVE/COE — no longer distinctive). **The expert gate was vindicated:**
   had we recalibrated the lens toward stage-down on the sonnet evidence, we would have been
   fixing a model artifact, likely over-correcting the fable-5 behavior.
4. **Effects compress under the stronger model.** W=0.04, Friedman p=0.76: at n=12 the six arms
   are statistically near-indistinguishable on Fable 5 — persona prompts matter *less* as the
   base model improves. (Descriptive wrinkle: the single-concern COS lens is now the best MJ
   matcher, 0.694.)
5. **Guards on reading this:** the model change confounds base-model capability with prompt
   effects; both runs are underpowered (n=12); cross-run deltas are exploratory. Also, fable-5
   rejects the `temperature` parameter, so arm sampling ran at model default (recorded in the
   manifest as an uncontrolled difference). Two stale progress-print strings in
   `phase2_analyze.py` still say "gpt-4.1"/"claude" — the models actually used are config-driven
   (gpt-5.5 / claude-fable-5); cosmetic only.

### Standing decision (updated)
Unchanged, and strengthened: **record the negatives; do NOT change the lens.** The one concrete
new lesson is methodological — *any* future lens change must be validated across ≥2 base models
before being believed, because the failure mode itself proved model-dependent.
