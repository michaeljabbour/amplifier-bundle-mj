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

## Files
- Dashboard: `results-summary/dashboard.html` (open in a browser)
- Numbers: `results-summary/aggregate.md` / `aggregate.json`
- Raw runs (transcripts, per-dimension reasoning, council verdicts, gitignored):
  `~/.amplifier/evaluation/occams-vs-council/20260701T070714Z/`
