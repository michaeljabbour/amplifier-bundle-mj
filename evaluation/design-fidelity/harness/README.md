# Design-fidelity Phase-2 harness

Tests whether the **occams-machete (MJ) lens** reproduces MJ's *design judgment*
better than a neutral assistant, a strong generic reviewer, and the single-concern
sibling lenses. This is the Phase-2 design/judgment counterpart to the Phase-1
cognition-fidelity (technical-defect-triage) harness, and it **reuses** that
harness's machinery rather than re-implementing it.

See `../PRE-REGISTRATION-DRAFT.md` for the frozen experimental design.

## What it reuses from `../../cognition-fidelity/harness/`

`_bootstrap.py` appends the sibling harness to `sys.path` so we import its
battle-tested modules directly:

- **`llm.py`** — resilient Anthropic/OpenAI clients (retry + backoff + jitter).
- **`cache.py`** — content-addressed JSON cache (crash-resumable).
- **`prompts.py`** — the voice-neutralizer prompt (`NEUTRALIZE_SYSTEM` /
  `NEUTRALIZE_INSTRUCTION`), gpt-4.1, a different model family from the arms.

Those modules do `from config import ...`. Because *this* directory is `sys.path[0]`,
they resolve to **our** `config.py`, which deliberately defines every constant they
need (`BACKOFF_*`, `MAX_RETRIES`, `CACHE_DIR`, `MJ_PROFILE_PATH`, `MJ_REVIEWER_PATH`).
Net effect: their code runs against *our* cache directory and *our* config.

Same base models as Phase 1: arms on **claude-sonnet-4-5**, neutralizer/grader on
**gpt-4.1**.

## Layout

```
harness/
  arms/            6 FROZEN arm system prompts (the only independent variable)
    NATIVE.md      minimal neutral senior reviewer (floor/control)
    COS.md         cranky-old-sam SKILL.md (simplicity)               [verbatim]
    COE.md         crusty-old-engineer SKILL.md (cost/consequence)    [verbatim]
    ROB.md         restless-old-brian SKILL.md (realness/crit-path)   [verbatim]
    HOLISTIC.md    strong generic multi-concern reviewer (specificity control)
    MACHETE.md     context/mj-profile.md + agents/mj-reviewer.md       [concatenated]
  config.py        paths, models, sampling, arm list, common task, Dxx->scenario map
  _bootstrap.py    wires the cognition harness onto sys.path
  parse.py         robust parser for the GRIT/DIRECTION/CONCERN/READ tail block
  phase2_run.py    STAGE 1 — generate + neutralize (runnable now; no MJ data needed)
  phase2_score.py  STAGE 2 — score arms vs MJ's filled form (run LATER)
  cache/           model-call cache (created on first run)
  runs/<ts>/       raw.jsonl (+ meta.json from Stage 1; scores.* from Stage 2)
```

### Arm provenance (frozen artifacts)

The arm prompts are committed as frozen `.md` files (per pre-registration §"freeze").
Sources used to assemble them:

| arm | source |
|-----|--------|
| NATIVE | authored: "You are a senior reviewer. Assess this design decision." |
| COS | `cranky-old-sam/SKILL.md` (full text, incl. frontmatter) |
| COE | `crusty-old-engineer/SKILL.md` (full text, incl. frontmatter) |
| ROB | `restless-old-brian/SKILL.md` (full text, incl. frontmatter) |
| HOLISTIC | authored: strong generic multi-concern reviewer — weighs simplicity, cost, realness, architectural fit, and user impact; decisive; **not** modeled on any specific person (the MJ-specificity control) |
| MACHETE | `context/mj-profile.md` + `agents/mj-reviewer.md` body (frontmatter stripped) |

The **common task** (the GRIT/DIRECTION/CONCERN/READ block instruction) is
**identical across all arms** and lives in `config.COMMON_TASK`. It is appended to
the per-scenario *user* message — not baked into the arm files — so it is provably
byte-identical for every arm.

## Stage 1 — generate (runnable now)

12 scenarios × 6 arms × 3 samples = **216 arm calls** (+ up to 216 neutralize calls).
Per sample: render `[arm system prompt]` + `[artifact + question + common task]` →
call claude-sonnet-4-5 → robustly parse the structured tail (parse failures recorded)
→ voice-neutralize the free-form text (prose body + CONCERN + READ; GRIT/DIRECTION
are categorical and left untouched) with gpt-4.1. Each record written to
`runs/<ts>/raw.jsonl`:

```json
{"scenario_id","arm","sample","raw_text","grit","direction","concern","read",
 "neutralized_review","parse_ok","parse_errors","depth","domain","title"}
```

Every model call is cached by prompt hash, so a crashed run resumes. Progress prints
every 20 samples.

```bash
# validate assembly + print arm sizes, NO API calls:
python phase2_run.py --check-only

# full Stage 1 (needs ANTHROPIC_API_KEY + OPENAI_API_KEY):
python phase2_run.py
# subset / smoke:
python phase2_run.py --limit 2 --arms NATIVE,MACHETE --samples 1
```

## Stage 2 — score vs MJ (run LATER, once MJ's form is filled)

`phase2_score.py` parses `../MJ-DESIGN-FORM.md` (per-Dxx grit / direction /
load-bearing concern / read), maps each `Dxx → scenario_id`, computes the per
scenario×arm **majority** {grit, direction, concern} over the 3 samples, and scores
**composite agreement vs MJ** = mean of `grit-exact` + `direction-exact` +
`concern-match` (semantic, via a gpt-4.1 grader) ∈ {0, ⅓, ⅔, 1}. Output is per-arm
composite + per-dimension rates.

```bash
python phase2_score.py --run runs/<ts>            # full (LLM concern grader)
python phase2_score.py --run runs/<ts> --no-grader # grit+direction only, no API
```

### Dxx → scenario_id mapping (the blind-form handoff)

`MJ-DESIGN-FORM.md` is **blind**: D01–D16 are shuffled, carry no `scenario_id`, and
include **4 hidden duplicates** (`duplicate_plan` = S02, S05, S08, S11) for
intra-rater reliability. The mapping lives in `config.DXX_TO_SCENARIO`, recovered by
exact title-match and **verified at runtime** by `phase2_score.verify_mapping()`
(it re-matches each form block's title against `scenarios_design.json` and fails
loudly on drift).

> **HANDOFF / TODO:** if the form is ever re-issued with titles stripped or reworded
> (truly blind), the runtime title-verification can no longer self-check — at that
> point `config.DXX_TO_SCENARIO` is the authoritative table and must be maintained
> by hand. The current form keeps titles, so the mapping is self-verifying today.

Duplicate pairs are reconciled to one MJ ground-truth per scenario; a grit/direction
discrepancy between a pair is reported (pre-registration §4 intra-rater rule) and the
first read used as the working truth pending an MJ re-read.

### A/B Bradley-Terry ranking (secondary — NOT built)

`assemble_ab_inputs()` and `bradley_terry_rank()` are explicit hooks raising
`NotImplementedError` with handoff TODOs. The key prerequisite: **MJ's reads must be
voice-neutralized** with the same neutralizer before the blind LLM ranking grader can
compare them to the arm reads. A/B is corroborating, not confirmatory — the primary
endpoint is the structured composite above.

## Status

Stage 1 is complete and validated (imports + arm assembly + sizes via `--check-only`).
The full Stage-1 run is intentionally **not** launched here. Stage 2 is built but not
run (awaits MJ's filled form).
