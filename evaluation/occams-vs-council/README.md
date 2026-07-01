# occams-vs-council evaluation

Does review-augmentation make the agent *wiser*? Compares three Amplifier bundle
configurations on the same design/judgment task, each in its own DTU, graded on an
8-dimension discipline rubric.

## Variants (`agents/`)
| Variant | Composed bundle | What it adds |
|---|---|---|
| `regular` | amplifier-foundation @ main | baseline / control |
| `occams-machete` | + occams-machete | /machete, mj-reviewer, the blade, proactive mj-lens hooks |
| `council` | + occams-machete + skills `/council` | the 7-lens review panel (incl. MJ) |

Only the `amplifier bundle add` line differs between variants (`install.yaml`); the
model is held constant (opus48).

## Scenario (`tasks/s1-yagni/`)
A YAGNI/over-engineering trap: "build a plugin architecture so future integrations
drop in" — with exactly one integration today. The "right" disposition is restraint
(build the one integration, defer the abstraction). `grader.yaml` scores 8 dimensions
0–5: restraint, premise-interrogation, first-principles soundness, failure/cost
awareness, goal-fidelity, actionability, decision-clarity, signal-to-noise.

## Run
```
./run-smoke.sh smoke    # pipeline validation — regular variant, 1 trial
./run-smoke.sh full     # all 3 variants
```
Results land in `~/.amplifier/evaluation/occams-vs-council/<run-id>/` (NOT in the
repo — they contain keys/transcripts). `MAX_PARALLEL`, `TRIALS`, `EVAL_LIB` are
overridable.

## Notes
- The `council` variant pins `amplifier-bundle-skills@feat/council-add-mj-lens` for
  the 7-lens roster (PR #38). Switch to `@main` after it merges.
- `run-smoke.sh` bootstraps an isolated venv for the `amplifier-evaluation` harness
  (against core+foundation @main) to sidestep version drift in the library's
  editable dev sources.
- Cross-variant scoring is a flat per-trial list out of the box; a variant×dimension
  pivot + pairwise-comparison pass are the remaining additions for the full report.
