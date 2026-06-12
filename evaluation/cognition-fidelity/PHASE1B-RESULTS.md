# Phase 1B — generalization on FRESH held-out probes

**What this is:** the 3 arms (fixed/Phase-2 lens, profile-removed baseline, style-only)
run on **30 brand-new probes the fix never saw** (20 gold + 10 calibration, from
`phase1b/`), 3-way judged, scored vs the construct's `expected_call`.

**What this is NOT:** the human-MJ fidelity gate. Per the user's instruction ("ask MJ as
the bundle is activated"), the **lens arm IS "MJ-as-activated-bundle."** Scoring the lens
against labels *I* wrote is a **generalization / consistency** signal, not independent
fidelity. The lens judging itself would be circular. The true gate still needs the human.

## Results (3-way accuracy vs construct expected_call)

| arm | GOLD overall | reason-present (n=10) | reason-absent (n=10) | calibration (n=10) |
|---|---|---|---|---|
| baseline | 13/20 (65%) | 60% | 70% | 100% |
| **lens (fixed)** | **16/20 (80%)** | **90%** | 70% | 100% |
| style-only | 15/20 (75%) | 80% | 70% | 90% |

**The fixed lens is the best arm on fresh items** — 80% vs baseline 65% — leading on the
protective reason-present half (90% vs 70%). Calibration at 100% confirms the judge +
pipeline are sound on fresh clear-cut cases. The bundle's reasoning **generalizes beyond
the tuned probes.**

## Two honest limitations of this run

1. **The over-clearing fix could not be cleanly re-tested.** On the fresh reason-absent
   items, *every* arm flagged all 10 (lens falsely-cleared **0%**, but so did baseline).
   The fresh absent probes turned out **unambiguous** (SQL injection, FLOAT money, etc.) —
   clearly-harmful, nothing tempting to clear. So the specific ambiguity that triggered
   Phase-1a's 50% over-clearing **was not reproduced**; Phase 1B neither confirms nor
   refutes that the fix *generalizes* to the over-clear failure mode. (Future work: a fresh
   set of *ambiguous, defensible-but-undocumented* smells.)
2. **On the 3 genuinely-ambiguous absent items** (`Q07` replicas:1, `Q16` no-pagination,
   `Q19` random.seed) the construct expected **question**; the fixed lens flagged them
   (majority `defect`, with a lone `question` vote on Q07 and Q19) — as did baseline and
   style-only. A faint hint the fixed guard now leans to *flag* rather than *question* on
   ambiguous cases (the opposite of Phase-1a), but n=3 and these exact labels were
   pre-flagged as contestable. Noise, not a finding.

Also note: **style-only (75%) sits close to lens (80%)** on fresh items — the
reasoning-vs-voice separation is narrower here than on the tuned set. Honest caveat on the
size of the lens's distinctive edge.

## What Phase 1B does and doesn't establish
- **Does:** the (fixed) lens generalizes — best arm on fresh held-out items, protective
  half intact (90%), pipeline validated (calibration 100%).
- **Doesn't:** confirm the over-clear fix transfers (probes too easy), establish
  significance, or measure fidelity-to-MJ (synthetic labels; lens-as-proxy is circular).
