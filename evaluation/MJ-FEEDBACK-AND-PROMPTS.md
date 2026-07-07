# MJ's feedback to the evaluation team — and a record of every prompt

> Compiled by the assistant from a 31-turn evaluation session (2026‑06‑12). The
> feedback below is written in MJ's voice from what he said and did across those
> turns; **MJ should edit/endorse it.** Per this directory's policy (see
> `evaluation/README.md`), the verbatim prompt transcript and session ID live with
> the untracked run outputs, not in source control — Part B below summarizes the
> arc and says where the verbatim record lives.

---

## Part A — Feedback to the evaluation team

### The one‑line version (MJ's words)
> *"It took me a long time to even get here and we aren't yet even there."*

After 31 turns and a lot of my time, the honest state is: we built a rigorous
evaluation, it produced a credible **negative** (the MJ‑lens came last on the design
benchmark), and we **still don't have a validated answer or an improvement to the
bundle** — the next move is *more* gated work (a grit‑referent check, then a fresh
~30‑scenario hold‑out). That's intellectually honest. It is also a long road for the
payoff so far.

### What cost the most time: the eval kept aiming at the wrong target
This is the headline lesson. We measured the wrong thing **twice** before measuring
the right thing:
1. The first evals measured **code‑reduction mechanics** — treating occams‑machete
   as a code tool. It isn't.
2. Then we built an entire multi‑phase **cognition study** (Phases 1a / 2 / 1b) on
   the *anti‑conflation guard* — found and fixed a real bug, ran a 34‑question human
   exam — and only *after* I sat that exam (turn 21) did we agree it was **"really a
   technical coding eval,"** not a test of what the bundle is *for*: my design
   judgment, logical audits, PM mindset, "the way MJ would do it."
3. The **actual** design benchmark didn't start until turn 22 of 31.

I flagged this early — turn 4 ("your rubric and A/B seem to have no helpful data or
measurement based on what it was supposed to do") and turn 8 ("it is designed to
mimic my process and cognition … I didn't see any of that in the evaluation"). That
signal should have **re‑routed the whole effort immediately**, not after a full
study was built, frozen, and human‑graded.

**Ask of the eval team:** before building any harness, pin the target with the
bundle's author/expert — *"what is this thing FOR, and what would success look
like?"* — and treat "this isn't measuring the purpose" as a **stop‑and‑re‑route**
signal, not a note to address later. Distinguish the **mechanism** of a tool from its
**purpose**; we burned the most time on that gap.

### Human time was heavy, and front‑loaded onto me
I did **34 cold reads** (Phase 1b) **+ 16 cold reads** (design benchmark), plus
repeated "did you actually update X?" checks. A lot of that was spent on the eval
that turned out to be the wrong target. If the target had been pinned first, most of
the Phase‑1 human grading wouldn't have been needed.

**Ask:** budget and *sequence* human‑in‑the‑loop time deliberately. Say up front
that "does this reproduce a person's judgment" evals are inherently long and need the
person — and don't spend the person's grading budget until the target is confirmed.

### Trust/verification friction
Three separate times I had to ask "did you update the dashboard / files / sessions?"
(turns 16, 29, and again at the end) — and more than once the answer was "done" when
files were actually stale. The work got corrected each time, but **I shouldn't be the
freshness check.**

**Ask:** the harness/assistant should self‑verify artifact freshness (and say what's
current vs. stale) *before* claiming done — not after being challenged.

### "Less is more" applies to the eval itself
The cognition study spun up sub‑phases (1a / 2 / 1b, a symmetric‑guard fix, a
generalization run) that produced a clean fix **on an axis that turned out not to be
the point.** Fewer, higher‑signal phases aimed at the real purpose would have gotten
us here faster. (Ironically, the design benchmark then found the *lens* itself
over‑elaborates — the 303‑line MACHETE prompt lost to an 85‑line generic one. The
"less is more" lesson cuts at every level here.)

### What genuinely went well (credit where due)
- **Rigor held and honesty won over spin.** Pre‑registration, freezes, controls, and
  a real human reference standard let a **credible negative** land instead of a
  flattering story. That's the point of evaluation.
- **The assistant caught its own errors** — a parse‑bias that had unfairly penalized
  the lens, and a scipy bug that faked a p‑value — and corrected them rather than
  shipping them.
- **Experts were consulted before acting** (amplifier, foundation, research
  methodologist + statistician), and the consensus — *record the negative, don't
  change the lens yet, gate the fix* — kept us from overfitting to 12 scenarios.

### Net
The destination is honest and the machinery is sound. The **path** was too long
because the target wasn't pinned to the bundle's purpose up front, and too much of my
time was spent grading the wrong eval. If the team takes one thing: **confirm what the
bundle is for, and what success looks like, before building anything — and treat the
author saying "this isn't measuring the purpose" as an emergency re‑route.**

---

## Part B — The prompt record (where it lives)

Per this directory's policy (`evaluation/README.md`), run artifacts — verbatim
transcripts, session IDs, absolute local paths — are **not** source-controlled.
The verbatim record of all 31 prompts stays with the untracked evaluation run
outputs (the local eval package alongside the dashboards, and
`~/.amplifier/evaluation/…`).

The shape of the 31 turns, summarized:

1. **Turns 1–3 — kickoff.** Evaluate the bundle; MJ endorses an A/B + rubric
   approach; environment brought up.
2. **Turns 4–11 — target correction.** MJ flags twice (turns 4 and 8) that the
   eval measured *mechanics*, not the bundle's *purpose* (his design judgment,
   logical audits, PM mindset); redesign is requested, hardened (more trials,
   more axes), and greenlit.
3. **Turns 12–21 — cognition study build-out.** Phases 1a/2/1b, dashboards,
   repeated freshness challenges ("did you actually update X?" — turns 16–17),
   MJ sits the 34-question exam and questions its framing.
4. **Turns 22–28 — the real design benchmark.** Reset onto design cognition:
   synthetic scenario construction, expert confirmation, MJ answers all 16
   scenarios with ship/tweak/redesign/kill calls and grit ratings.
5. **Turns 29–31 — closeout.** Final freshness check, review of the story
   dashboard, and the closing ask that produced this file.
