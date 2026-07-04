# Evaluations

Studies measuring what the Occam's Machete bundle actually does. Each study is
self-contained in its own subdirectory — fixtures, agents, tasks, graders, harness, and
written-up results.

> Run outputs (transcripts, model responses, absolute paths) are **not** source-controlled;
> they land under `~/.amplifier/evaluation/…`. Only harnesses, fixtures, and results live here.

| Study | Question it answers | Highlights |
|---|---|---|
| [`occams-vs-council/`](occams-vs-council/) | Does review-augmentation make the agent *wiser* — and is the heavier council worth it over the machete alone? | Plain vs **+machete** vs **+council** across design and code tasks, graded on an 8-dimension discipline rubric. **The machete wins; the council never pays off.** See its [`RESULTS.md`](occams-vs-council/RESULTS.md). |
| [`reduction-ab/`](reduction-ab/) | Does the machete cut more genuinely-removable weight while refusing to cut from a red baseline? | A/B: baseline vs machete on the `pulse` / `flowforge` fixtures (`reduce-green` / `reduce-red` / `reduce-hard`). |
| [`design-fidelity/`](design-fidelity/) | Does the MJ / machete lens improve *design-cognition* over a native agent? | Pre-registered benchmark (v2): 6 arms incl. HOLISTIC, Wilcoxon `MACHETE > NATIVE`, product/strategy + team/process domains. |
| [`cognition-fidelity/`](cognition-fidelity/) | Is a "faithful" reasoning result real, or an artifact of the setup? | Pre-registered, frozen Phase-1 study using a commitment-device methodology (frozen profile, probes, rubric, and judge). |

Each subdirectory has its own README with method, how-to-run, and grading details.
