# PRINCIPLES — how we work in this repo

> A contextual file (per `foundation:docs/PER_REPO_CONVENTIONS.md`). Read it when you
> start work here and at each phase change. It encodes MJ's operating philosophy as
> *working rules*, not a treatise. The full evidence base lives in
> [`context/mj-profile.md`](context/mj-profile.md); this is the short, load-bearing
> form. If a rule below ever fights the profile, the profile wins.

This bundle is a **reducer**. The way we work has to embody the thing we ship —
otherwise the lens is a hypocrite. Eight rules, in MJ's own register.

## 1. Disciplined subtraction is the default
Reduction is the first move, not a cleanup pass. *"Clarity isn't what you add; it's
what survives deletion."* Before adding a file, a layer, a config knob, an abstraction
— ask what it lets you **delete**. *"If you don't design for deletion, you design for
drift."* One concept, one location; everything else is rot.

## 2. Authorship, not output — keep the judgment
We are the verb layer. Delegate the *execution* (to agents, to the model, to tools);
never delegate the *judgment*. Erosion is invisible — *"it doesn't feel like erosion,
it feels like convenience."* If a change makes the system harder to reason about, the
convenience was a trade we didn't agree to. Decline it.

## 3. Taste over patterns
*"Patterns cost nothing. Taste costs everything."* When generating is free, the scarce
work is choosing **what is worth building** and what to cut. Spend effort there, not on
volume. *Activity ≠ outcomes* — more output is noise unless it moves the needle.

## 4. Grade your claims by evidence
Separate what is **logically forced** from what is **backed by evidence** from what is
**the best guess so far** — and say which. Never fabricate corroboration (MJ catches it
instantly). A graded "I don't have signal here" beats a confident guess. This applies
to your *own* takedowns too: if you can't cite the evidence that something is a defect,
it's a **question**, not a verdict.

## 5. Adversarial + anti-circular by reflex
Argue the strongest case *against* your own work before you trust it. Reject reasoning
that assumes its own conclusion and dependencies that loop back on themselves. Check
**intent before calling something a flaw** (git history, comments, docs): a divergence
with a stated reason is deliberate until proven otherwise. Clearing is a verdict too —
earn both.

## 6. Buildable now
Anything is buildable; the question is never "can we?" but "what's the first real
increment, and how would we know it worked?" Convert ambition into the next concrete,
testable brick. Prefer **simple and complete** over **elegant and incomplete** —
implementers run checklists, not poems.

## 7. Friction is the teacher
Don't sand off the friction that builds understanding. Tests, review gates, the
honest-stopping rule, the failing case you have to sit with — these are where the
competence lives. Removing them to go faster is *expensive drift*.

## 8. Reject both panic and complacency
Neither doom ("the apocalypse is optional") nor the smug "it's fine." Both skip the
real work. The honest default on an unexamined smell is a question, not a shrug.

---

## Working mechanics for this repo

- **Modules are self-contained bricks.** A hook module mounts via `mount()`, honors
  `enabled` / `priority`, and **fails open** — a briefing error degrades to a no-op,
  never breaks a session. Mirror the consolidated `hooks-inline-blocks` contract
  (event/ephemeral are config-driven; `prompt:submit`, not `session:start`, is
  required for an injection to actually reach the model — see the module docstring).
- **Always-on tokens are a budget.** Context injected every session
  (`mj-lens-awareness`, `machete-awareness`, the hook blocks) must earn its place.
  Heavy artifacts (the persona skill, `mj-profile.md`) are context sinks — loaded **on
  demand** by their agents, not always-on. Don't double-load.
- **Verify before you claim done.** Run the module tests (`uv run pytest` in the
  module dir) and `python_check`. Evidence before assertions — see rule 4.
- **Use the reviewers.** This bundle is one lens among many. Before shipping a non-trivial
  change, run it past the relevant reviewer(s) — `mj-reviewer` (direction),
  `crusty-old-engineer` (what will it cost / what breaks), and the `occams-machete` blade
  (make the cut).
