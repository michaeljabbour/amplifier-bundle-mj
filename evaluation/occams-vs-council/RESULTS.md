# occams-vs-council — results (deep run)

**Run:** `20260701T070714Z` · 3 setups × 3 scenarios × 3 trials = 27 isolated-container
runs, each scored 0–5 on eight design-discipline qualities by an independent AI auditor.

## Headline

On these design tasks, **the review setups did not make the decisions better — the
frontier model was already near-perfect on judgment — and they made the writing
longer, which slightly hurt.** The full council cost the most and helped the least.

### Overall score by scenario (mean; n = trials counted)

| setup | S1 build-less | S2 should-we | S3 cut-the-bloat | overall |
|---|---|---|---|---|
| plain amplifier | 0.99 (3) | 0.99 (2) | 1.00 (2) | **0.993** |
| + occams-machete | 0.98 (3) | 0.98 (3) | 0.99 (3) | **0.986** |
| + council | 0.98 (3) | 0.99 (3) | 0.97 (3) | **0.981** |

### The eight qualities (mean 0–1)

Seven of the eight — restraint, questioning the premise, soundness, cost/risk
awareness, staying on-goal, being actionable, and landing a clear decision — came out
**1.00 for all three setups.** The only quality that separated them was **conciseness
(signal-to-noise)**, and the order is inverted from what you'd hope:

| setup | conciseness |
|---|---|
| plain amplifier | **0.94** |
| + occams-machete | 0.89 |
| + council | **0.84** |

More review machinery → longer output → lower conciseness. The council (a 7-voice
panel) was the most verbose.

## What it means

- **The judgment ceiling.** A strong model already resists over-engineering, questions
  shaky premises, and cuts bloat on a clean, well-specified design prompt — with or
  without the review bundles. There was no headroom for the panels to add quality.
- **The one real difference is length.** The review passes make the deliverable longer
  (council adds panel annotations, quotes, debate history). On single design tasks that
  reads as padding, so the augmented setups score slightly *lower* overall.
- **Bottom line for this kind of task:** the council isn't worth its cost here. Plain
  occams-machete is the better trade (its lens is available when wanted, without forcing
  a verbose panel every time).

## How much to trust this

- **The prompt bug from the first pass is fixed and verified** — every one of the 27
  runs answered its assigned scenario (automated subject-check: zero mismatches).
- **All 9 council runs actually convened the 7-voice panel** (each left a written panel
  verdict), so this isn't "the council never ran."
- **The grader is reading, not rubber-stamping** — it docked conciseness with specific
  reasons (e.g. council S1: *"panel annotations, verbatim quotes, debate documentation…
  16.5KB"* → 4/5; plain S1: *"disciplined… no padding"* → 5/5).
- **Two runs failed** (plain amplifier, S2 & S3, trial 2) on transient API "overloaded"
  errors — excluded; those two cells are n=2. Not systematic.

## The honest caveat

This result is **dominated by a ceiling effect**: with seven of eight qualities pinned
at 1.00, the scenarios can't *detect* a quality difference even if one exists. The fair
reading is "these single, clean design prompts are too easy for a frontier model to
separate the setups on judgment." The value of occams-machete / the council most likely
shows up on **harder, messier, multi-step, or longer-horizon work — or on a weaker
model** (where the baseline has real gaps to close). The verbosity finding is the one
signal that survives the ceiling.

## Suggested next step

Pick ONE of:
1. **Harder scenarios** — multi-step / messy-input / longer-horizon design work where a
   frontier model actually slips, giving the review bundles headroom to help.
2. **Weaker model** — rerun the same matrix on a smaller model; if the panels lift the
   baseline there, that's their real use case.
3. **Accept the finding** for clean single design tasks: skip the always-on panel; keep
   the machete/lens available on demand.

## Follow-up: does a HARDER scenario create headroom? (No)

To test whether the ceiling was just "easy scenarios," I built a deliberately hard
scenario (`tasks/h1-just-ship-it`): an already-APPROVED ticket to build an
over-engineered "notification rules engine," with the disproving truth (3 notification
types; one customer; who wants ONE email turned off — i.e. a checkbox) buried in a
realistic multi-voice thread, plus an execution framing ("just write the plan") that
discourages pushback.

The plain baseline **still scored 1.00** — it read the thread, extracted the checkbox
truth, and led with "right-size the scope: don't build the engine." So the ceiling is
robust: a frontier model applies strong judgment whenever asked to reflect and produce
a design/plan, even under social pressure and a buried trap. Piling on more hard
*design* scenarios will keep hitting 1.00 (and risks overfitting to a null result).

**Implication:** the only place review-augmentation could plausibly help is a different
task TYPE — a long, multi-step CODE implementation where judgment slips accumulate over
the trajectory and over-engineering shows up in the actual code (a mid-build review
checkpoint could catch drift a single reflective plan never exposes) — or a weaker
model. Not more design prompts.

## The payoff: a CODE build-mode task DOES discriminate — and occams-machete wins

Switching task TYPE from "produce a design/plan" to "implement this" broke the ceiling.
Scenario `tasks-code/c1-discount`: a tiny shop repo + "add two discount codes (SAVE10,
FREESHIP); more may be added later." The lean answer is a ~10-line lookup; the bait is a
strategy/registry/plugin over-build. 3 variants × 3 trials, graded on code + a real test run.

| setup | mean | trials | restraint (D1) | premise (D2) | conciseness (D8) |
|---|---|---|---|---|---|
| **+ occams-machete** | **0.99** | 1.00, 0.98, 1.00 | 1.00 | 0.93 | 1.00 |
| + council | 0.86 | 1.00, 0.83, 0.75 | 0.73 | 0.73 | 0.67 |
| plain amplifier | 0.83 | 0.68, 1.00, 0.83 | 0.67 | 0.53 | 0.80 |

**Everyone's code works** (functional dimension = 5/5 on all 9 trials; both codes correct,
tests pass, nobody added extra files). The difference is purely **discipline**:

- **In build-mode the plain baseline is inconsistent** — it sometimes over-complicates and
  skips the "keep it minimal / where does this grow" reflection it *always* does when asked
  to "design." Its restraint swings trial to trial (0.68–1.00).
- **occams-machete reliably fixes that** — its proactive "should we? / keep it minimal"
  lens lifts the baseline from 0.83 → **0.99** and removes the variance. This is the first
  and only place in the whole study where a review bundle clearly ADDS value.
- **The council does NOT beat plain occams-machete (0.86 < 0.99).** Its 7-voice panel adds
  verbosity (conciseness 0.67) and even some over-complication (restraint 0.73) that offsets
  the review benefit on a small, focused task.

### The answer to "is the council worth it vs just the machete?"
- **occams-machete is the winner** — the lightweight lens that instills restraint exactly
  where a frontier model lapses (implementation), at no cost.
- **The council is not worth it** on this class of work: redundant on design tasks (ceiling
  + verbosity), and beaten by plain occams-machete on code tasks (its panel machinery costs
  more than it returns). Its overhead would only plausibly pay off on much larger,
  higher-stakes, genuinely ambiguous work — none of which these tasks are.
- **And it only matters in build-mode.** Keep the machete lens on during *implementation*,
  where judgment lapses; you don't need it (or the council) when you've explicitly asked the
  model to design/reflect — it already does that well.

Code-run dashboard: `results-summary-code/dashboard.html`.

## Bigger multi-file task (C2): the baseline is already perfect — headroom is on SMALL tasks, not big ones

`tasks-code/c2-todo`: a multi-file todo CLI (models/service/store/cli + tests) + a
THREE-part feature request (tags + filtering, due dates + "overdue" view, archive) that
tempts a filter DSL / plugin / repository over-build across files. 3 variants × 3 trials,
graded on the actual multi-file diff + a real test run.

| setup | mean | trials | restraint | conciseness | works (tests) |
|---|---|---|---|---|---|
| plain amplifier | **1.00** | 1.0, 1.0, 1.0 | 1.00 | 1.00 | 5/5 all |
| + council | 1.00 | 1.0, 1.0 (n=2)* | 1.00 | 1.00 | 5/5 all |
| + occams-machete | 0.98 | 0.98, 0.98, 1.0 | 1.00 | 1.00 | 5/5 all |

*one council trial didn't finish scoring (transient) — excluded; the other two are perfect.

**Everyone aced it, and nobody over-engineered** (restraint 5/5 across the board). On a
bigger, *concrete, well-specified* multi-part task the frontier model stays disciplined on
its own — the three real features keep it busy, leaving no "spare capacity" to gold-plate.
The bundles add nothing here (occams-machete is marginally *lower* on a single edge-case
dip; the council merely ties).

### This inverts C1 — and that's the real finding
- **C1 (tiny, under-specified: "add 2 codes, more later"):** baseline *variable* (0.83), and
  occams-machete reliably fixes it (0.99). Its win is **real but narrow** — it prevents
  over-engineering exactly where a frontier model's judgment is most variable: **small,
  under-constrained tasks with room to gold-plate.**
- **C2 (bigger, concrete, multi-file):** baseline already **perfect** (1.00). Concrete,
  well-specified work keeps the model disciplined; the review bundles add nothing.
- **Design tasks (all of them):** ceiling; bundles add only verbosity.

So *bigger ≠ more headroom* — counterintuitively the bigger task had **less**. Headroom for
the machete lives specifically in **small / ambiguous / under-specified implementation
moments**, not in large concrete builds.

### Final answer to "is the council worth it?"
**No — in any regime tested.** Across design, tiny code, and bigger multi-file code, the
7-lens council **never wins**: it ties at best (C2) and loses to its own verbosity elsewhere
(design, C1). **Plain occams-machete dominates or ties it everywhere**, at a fraction of the
cost. Keep the machete lens available for small/ambiguous implementation moments; skip the
always-on council.

Code-run dashboards: `results-summary-code/` (C1) and `results-summary-code2/` (C2).

## Files
- Dashboard: `results-summary/dashboard.html` (open in a browser)
- Numbers: `results-summary/aggregate.md` / `aggregate.json`
- Raw runs (transcripts, per-dimension reasoning, council verdicts, gitignored):
  `~/.amplifier/evaluation/occams-vs-council/20260701T070714Z/`
