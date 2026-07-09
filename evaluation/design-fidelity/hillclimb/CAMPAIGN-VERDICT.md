# Hill-climb campaign — FINAL VERDICT (2026-07-07)

**Stop rule fired:** Tier-1b screen budget exhausted (2 of 2 uses), 0 gate clears. Per the
pre-registered protocol, the campaign closes with the pre-committed outcome:

## The hill is flat at the frontier — and here is exactly what that means (and doesn't)

**The evidence (2 rounds, 6 independently-authored variants, firewalled, ~0 noise floor):**

| round | variant | strategy | composite vs champion 0.556 | gate |
|---|---|---|---|---|
| 1 | V1_MVI | champion + stage-down anchor | −0.083 | FAIL |
| 1 | V2_LEAN | 7→4 moves, de-processed | −0.139 | FAIL |
| 1 | V3_COSHYBRID | ¼-size distillation | **±0.000 (exact tie)** | FAIL (no gain) |
| 2 | V4_DIRCAL | V3 + verdict-calibration rubric | −0.028 | FAIL |
| 2 | V5_STAGE | V3 + two-sizes-one-verdict staging | ±0.000 | FAIL (no gain) |
| 2 | V6_MERGE | V3 + both, woven | ≈0.000 (net −1) | FAIL |

Because the A/A calibration showed fable-5's measurement noise is ~zero (F=0.000, 11/12 exact
ties on identical-arm resample), **these ties and losses are real, not noise.**

**The three findings that explain "zero value":**
1. **The prompt is not the attached lever.** All 6 variants — different sizes, different
   strategies, different authors' passes — lost scenario S01 by the identical margin and won S03
   by the identical margin. When every mutation in the search space fails identically on the same
   inputs, the behavior is coming from the **base model's own judgment**, not the persona text.
2. **Direction misses are genuine judgment differences, not rubric confusion.** V4 carried an
   explicit verdict-referent rubric (the exact fix hypothesized for the direction axis) and
   direction-exact stayed at 4/12 — the same as everyone. The remaining MJ-gap lives in calls
   where MJ is genuinely contrarian relative to the model's priors (e.g., killing outright what
   the model would merely question).
3. **Most of the champion prompt is inert for one-shot fidelity.** A 4.9k-char distillation (V3)
   exactly matches the 19.2k champion, and adding targeted guidance to either does nothing or
   hurts. On a frontier model, the system prompt seasons the voice; the model cooks the verdict.

**What "zero value" does NOT mean:**
- Not "the bundle is worthless" — concern-identification is strong (9–10/12) across all lens
  versions, and the interactive/blade use-mode was never what this measured.
- Not "MJ-fidelity is impossible" — it means *prompt-text mutation on fable-5, measured one-shot
  at n=12,* cannot move it. The untested levers: base-model choice, few-shot examples of MJ's real
  calls (needs fresh labels + leakage care), fine-tuning, and interactive use.
- Not a wasted campaign — it produced a **real Pareto win**: **V3_COSHYBRID delivers identical
  fidelity at ~25% of the champion's size** (−14.3k chars of context every load), with 0 concern
  losses and slightly better grit. That is a shippable reduction candidate (validate in
  interactive use before adopting).

## Campaign cost accounting
- MJ's additional time spent: **zero** (the sealed lock set was never needed — no challenger
  earned it). The entire campaign ran on machine time.
- The protocol's guards all earned their keep: the A/A calibration flipped the primary-model
  choice before it corrupted every comparison; the firewall kept 6 variants label-clean; the
  pre-committed stop rule prevented an unfundable round 3 on wording two rounds proved inert.

## Recommendations (in order)
1. **Take the V3 Pareto win through interactive validation** (the machete's own medicine: same
   result, quarter the weight).
2. If more fidelity is genuinely wanted, the next honest lever is **few-shot MJ exemplars or
   fine-tuning** — a different campaign with a fresh pre-registration, not more prompt wording.
3. Keep the standing rule: any lens change validates across ≥2 base models.
