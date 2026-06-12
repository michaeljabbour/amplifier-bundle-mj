# MJ's feedback to the evaluation team — and a record of every prompt

> Compiled by the assistant from session `5d3d969f-072c-480f-b70e-0d40b6eba7b5`
> (2026‑06‑12). The feedback below is written in MJ's voice from what he said and
> did across 31 turns; **MJ should edit/endorse it.** The prompt record (Part B) is
> verbatim.

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

## Part B — Verbatim record of all 31 prompts

*(Session `5d3d969f-072c-480f-b70e-0d40b6eba7b5`, in order, exactly as entered.)*

**1.** `evaluate occams machete bundle`

**2.**
```
1. you can look through my sessions and find lots of examples of that, you can also consult with occams-machete directly about that
2. I like the A/B and rubric base
```

**3.** `docker is up`

**4.**
```
Ask MJ what the purpose of occams-machete is. Your rubric and A/B seem to have no helpful data or measurement based on what it was supposed to do.

Make me a "what went wrong in building and running the evaluation harness"  along with a description of what I told you do + info about the thing you are evaluating. Output in markdown in the ~/downloads directory
```

**5.** `can you fix the rubric, eval, and see what we can really do together?`

**6.**
```
yes generate the html dashboard, also identity and additional failures with session analyst, and clear non-jargon results in a mardown file in downloads. also display the summary of your findings and recommendations here
```

**7.** `open the html`

**8.**
```
1. fix the weak promise, increase the trials to 30, and harden the axes, 2. look at the real structure of the bundle with the amplifier experts. it is design to mimic my process and cognition (logical abstractions and audits, product manager mindset, and "the way mj would do it" - I didn't see any of that in the evaluation. please confirm, and then we can update
```

**9.**
```
1. I only gave you three axes, there are more in the bundle - I'm sure you an extrapolate, 2. you need to redesign your redesign, 3. I agree with a blend. I'm not worried about the cost. I am worried about statistically significant evidence even at a scall scale.
```

**10.** `muhc better, use amplifier scientist to answer those 4 questions`

**11.** `confirmed, greenlit, take as much time and inference as you need`

**12.**
```
1. proceed with recommendations, 2. I don't know how to answer those two questions - ask MJ directly as the bundle is activated, 3. you can build the html dashboard for all phases and just show what has completed
```

**13.** `open the html file. proceed with recommendations`

**14.**
```
commit the remainder. also have the amplifier scientist pull all the data and session work of this session and your internal sessions in a directory in ~/downloads/ along with what worked well and what didn'
```

**15.**
```
1. I created an atlernative way to manage your dashboard here: - /Users/michaeljabbour/Downloads/occams-machete-eval-package/dashboard-story.html - 2. you should proceed with 1B and finish off the entire project with your recommendations and then make sure the latest version of all fils are in your package
```

**16.** `did you update dashboard-story.html and dashboard.html and all the other files in that directory`

**17.**
```
what does the scorecard in the story file still say not done? Scoreboard... Done
Blade contest — safety win (+0.17); "never cut from broken" exposed as weak
Done
Judgment apparatus — built, locked, validated by its controls
Done
Finding — the guard is lopsided: perfect vs false accusations, blind to false acquittals
In-sample
One-file symmetric fix — validated on the original 40 scenarios only
Waiting
Phase 1b human-MJ exam — 34 blind questions: 20 fresh, 10 calibration, 4 hidden duplicates. Sets ground truth, adjudicates the 4 residual clears, tests generalization
Queued
Mirror fix into the blade · harder scenarios for power · twin-pair exams for Sam / Brian / Crusty · "never cut from broken" as an enforced gate
```

**18.** `so what needs to be done? what do you need from me to close out the entire experiment`

**19.** `open it in typora and I will answer`

**20.** `open the folder`

**21.** `I filled out that form, but didn't see any real architecture, philosophical, or design questions per se, was that intentiona?`

**22.** `score and finish phase 1, just note that it is really a technical coding eval you built.... then after let's get the real design benchmark agreed and your rubric/test approach agreed and move on to that eval`

**23.** `1. construct synthetically, 2. both, 3. you can always compare deep and shall problems, technical and non-technical problems against amplifier-native, ROB, COS, COE, and occams machete`

**24.** `all those questions you should confirm with amplifier research`

**25.** `confirmed`

**26.** `give me full location of that form`

**27.**
```
All 16 answered. Summary of calls:

ship-as-is: D03/D12 (review policy — incident-proven, reversible), D04 (helper PR — reviewer nits are gold-plating), D08/D14 (retry config — textbook fix, idempotent)
tweak: D07 (Slack — pinned index only, skip taxonomy), D11 (delete stale flag + dead branch), D13 (version, but time-box v1 instead of "indefinitely")
redesign: D01 (pricing — pilot + WTP study before the bet), D05 (mode split — behavioral validation + incremental personalization first)
kill: D02 (platform without felt pain), D06/D10 (Neo4j before exhausting Postgres), D09/D16 (Reports sunset — top-decile revenue uses it), D15 (standup replacement — no measured problem)

Duplicate pairs got consistent grit/direction; grit ranges 0–2, nothing rated foundational since in every heavy case my actual recommendation was to stage or scope down the change.
```

**28.**
```
1. yes
2. ask the amplifier experts including the research expert
```

**29.** `did you update the dashbaord, dashboard-story, and all the data and sessions?`

**30.** `open the story dashboard`

**31.** `it took me a long time to even get here and we arent yet even there. can you create a file with my feedback to the evalution team and a record of all my prompts?`
