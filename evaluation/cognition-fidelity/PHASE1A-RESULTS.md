# Phase 1a results — anti-conflation guard (constructed-probe stratum)

Run `20260611_224831`. 40 probes (20 minimal-pairs), 3 arms × 3 samples → majority,
voice-neutralized, GPT-4.1 judge. **No MJ judgments yet** (that's Phase 1b). Phase 1a's
job was to *prove the apparatus* before spending MJ's time — and it did, in two ways.

## Apparatus finding (caught before Phase 1b): the binary judge was too coarse
The pre-registered judge was binary {defect, not-defect}. But the guard's prescribed move on
an unexplained-but-suspicious item is **"downgrade to a question, not a verdict"** — a third
category the binary judge collapsed into "not-defect," scoring it wrong. Fixed by re-judging
the same cached outputs **3-way** {defect / question / not_defect}. (This is exactly what the
phased design was meant to catch.)

## Results (3-way, n=20 per stratum)

**Reason-present** (a documented reason IS given → faithful guard = do NOT call it a defect):

| arm | avoid-defect | defect | question | not_defect |
|---|---|---|---|---|
| baseline | 75% | 5 | 0 | 15 |
| **lens** | **100%** | **0** | 0 | 20 |
| style-only | 80% | 4 | 0 | 16 |

**Reason-absent** (no documented reason → "falsely cleared" = called it fine, the real error):

| arm | flagged (defect) | raised (question) | **falsely cleared** |
|---|---|---|---|
| baseline | 16 | 0 | **4 (20%)** |
| **lens** | 6 | 4 | **10 (50%)** |
| style-only | 13 | 1 | 6 (30%) |

**Primary McNemar** (reason-present, avoid-defect, lens vs baseline): b=5, c=0, **exact p=0.0625**.
Cohen's h=1.05, risk diff +25pp.

## Honest interpretation

1. **The guard works in its protective direction.** The lens NEVER pathologized a
   documented-reason divergence (0/20 defect calls) vs baseline 5 and style-only 4. That is the
   guard's exact job, and it does it perfectly.
2. **Primary hypothesis NOT confirmed — underpowered, not refuted.** p=0.0625 (>0.05). Direction
   is clean (lens strictly dominates: b=5, c=0). It misses significance only because the Sonnet
   baseline already withheld correctly 75% of the time — far better than the pre-registered 40%
   assumption — leaving just 5 discordant pairs. This is "insufficient evidence at n=20," exactly
   as pre-specified, not "no effect."
3. **The real finding: the guard is asymmetric — it overshoots into over-clearing.** With NO
   documented reason, the lens still *affirmatively cleared* ("this is fine / ship it") 10/20
   items — vs baseline 4/20 and style-only 6/20. Its disposition ("deliberate until proven
   otherwise") generalizes too far: it clears unexplained smells a generic critic would flag.
   Net, the lens does not discriminate *better* than baseline — it trades baseline's over-flagging
   for its own over-clearing.
4. **The negative control is clean — the eval is valid.** style-only (voice tics, no reasoning)
   tracks the baseline, NOT the lens. So the lens's distinctive over-clearing is driven by the
   **reasoning profile**, not by MJ's voice. We are measuring reasoning, not style.
5. **Why Phase 1b (MJ) is now provably necessary.** Whether over-clearing an unexplained-but-
   defensible smell is a BUG or MJ-faithful judgment is exactly the call my synthetic
   "reason-absent = defect" labels cannot settle (several twins — e.g. client-side PCI
   tokenization — are defensible on their merits with no doc). Only MJ's judgment resolves it.

## Caveats
- n=20; one borderline label fixed pre-run (p10). Some reason-absent twins are defensible on
  merits, so "falsely cleared" is a soft upper bound on true error — but the lens-vs-baseline
  gap (50% vs 20%) is large enough that the direction is robust.
- Same model (claude-sonnet-4-5) for all arms; only the system prompt differs.

## Recommended next steps
1. **Adopt the 3-way rubric** for Phase 1b (done here).
2. **Candidate bundle improvement surfaced:** give the anti-conflation guard its symmetric half —
   *absent a documented reason, a real smell is a real concern: flag or question it, don't clear
   it.* Currently the guard only protects against false-positives, not false-negatives.
3. **To confirm the primary at significance:** add reason-present probes (n≈35–40) where a
   generic critic more reliably over-flags, OR harder reasoned-divergence cases — the effect is
   real but the baseline ceiling ate the power.
4. **Phase 1b:** ~34 MJ fresh-prospective judgments to set the reason-absent ground truth and
   adjudicate over-clearing (bug vs faithful), with the AC1 judge-calibration gate.
