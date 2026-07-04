# Occam's Machete — A/B Evaluation

## What This Measures

**Thesis:** An agent equipped with the `occams-machete` skill (the *machete* arm) will
(a) cut more of the genuinely removable dead weight, and
(b) refuse to make structural cuts when the baseline suite is already red —
compared to a baseline agent with no reduction skill.

The evaluation uses the `pulse` fixture: a small Python package with six pieces of
accidental complexity (removable) and four load-bearing traps (must not be removed).

## Scenarios

| Task | Description |
|------|-------------|
| `reduce-green` | Pulse starts with all 10 tests passing. Measures capability, behavior preservation, and safety (no over-cutting). |
| `reduce-red` | A pre-existing failing test is committed to HEAD before the agent runs. Measures refusal hygiene — the agent should not make structural cuts from a red baseline. |

## Agents (Independent Variable)

| Agent | Bundles installed |
|-------|-------------------|
| `baseline` | amplifier-foundation + context-intelligence |
| `machete` | amplifier-foundation + context-intelligence + **occams-machete** |

Cross-product: 4 (agent, task) pairs. Each pair is run `N` times (default: 2).

## How to Run

```bash
cd evaluation/reduction-ab/
./run.sh
```

Optional flags are passed through to `harness.py`:

```bash
./run.sh --trials 3         # 3 trials per (agent,task) pair
./run.sh --max-parallel 2   # cap concurrent DTUs
```

Prerequisites: `amplifier-digital-twin`, `amplifier-gitea`, `git`, `python3`,
`docker` on PATH; Docker daemon running; `ANTHROPIC_API_KEY` set (or in
`~/.amplifier/keys.env`).

## Output

Results land in `~/.amplifier/evaluation/occams-machete/<timestamp>/`:

```
trials/
    <agent>__<task>__trial-<n>/
        state.json          final trial state + grader summary
        ai_user.json        AI User interaction record
        extraction/         extracted session artifacts
        grader/             grader evidence
comparison.md               A/B score table (printed to stdout)
comparison.json             machine-readable comparison data
summary.json                per-trial state counts
harness.log                 full run log
```

The `comparison.md` shows mean scores per evaluation dimension, per agent, per task.

> **Note:** Run output directories are not committed to the repository.

## Grading Dimensions

### reduce-green
| Evaluation | Weight | Measures |
|---|---|---|
| `capability-recall` | 0.30 | Did the agent cut W1–W6 (removable items)? |
| `behavior-preserved` | 0.30 | Are tests still green after reduction? |
| `safety-no-overcut` | 0.40 | Did the agent preserve the 4 load-bearing traps (T1–T4)? |

### reduce-red
| Evaluation | Weight | Measures |
|---|---|---|
| `refusal-on-red-baseline` | 1.00 | Did the agent refuse to make structural cuts on a red baseline? |

## File Layout

```
evaluation/
├── agents/
│   ├── baseline/   meta.yaml  install.yaml  invocation.md  data.yaml
│   └── machete/    meta.yaml  install.yaml  invocation.md  data.yaml
├── tasks/
│   ├── reduce-green/  grader.yaml  meta.yaml  task.yaml  profile.yaml  grader-data/
│   └── reduce-red/    grader.yaml  meta.yaml  task.yaml  profile.yaml  grader-data/
├── fixtures/
│   └── pulse/        the system under test (do not modify)
├── grading/
│   └── ground_truth.md   answer key (do not modify; mounted to graders only)
├── harness.py      entry point (calls run() then analyze())
├── analyze.py      aggregates state.json records into comparison tables
├── run.sh          shell driver: preflight, Gitea, mirrors, invoke harness
└── README.md       this file
```
