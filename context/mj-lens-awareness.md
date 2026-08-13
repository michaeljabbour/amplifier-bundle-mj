# The MJ lens (awareness)

This bundle carries a model of how **MJ** (Michael Jabbour) thinks — so any session
can ask *"what would MJ think about this?"* and get a grounded answer instead of a
guess.

**When someone asks "what would MJ think?", wants an MJ-style gut-check, or wants an
idea pressure-tested before committing** → delegate to the `mj-reviewer` agent
(`mj:mj-reviewer`). It judges *shape* and *heading* — whether the thing
is pointed the right way, and how heavy a change it really needs. Different job from
the `occams-machete` agent, which executes the concrete cut: direction vs. execution,
not two copies.

The reviewer names the call, argues the strongest case against it, says how big a
change is actually warranted, and recommends the smallest step you could take first
and undo if it turns out wrong. Warm, blunt, brief. It sets direction; when the
answer is "cut it," `occams-machete` does the cutting.

Three ways in, and the difference is load-bearing:

| To judge | Use |
|---|---|
| An artifact you can name (file, diff, doc) | `delegate(agent="mj:mj-reviewer")` — forks a clean session |
| **This conversation** — the plan being built right now | `load_skill(skill_name="mj-lens")` — inline, sees the current context |
| A stretch of work, in review posture | `/mj` mode — blocks every mutating tool, so you can't drift into editing |

The agent cannot see this conversation; the skill can. Choose on that.
Deciding something worth citing later? `mj:recipes/direction-check.yaml` adds an
approval gate and records the call, its counter-argument, and your ruling.

**A different question, a different lens.** `mj:mj-reviewer` judges whether work
is *pointed the right way*. It will bless excellent work that answers a question
nobody asked. Before claiming done — or when a request has been through enough
turns to drift — use `mj:goal-keeper`, which judges only *was this what was asked
for*, treats an advisor's refusal as an unratified substitution, and calls
absence of evidence MISSING rather than DELIVERED. **Paste the request verbatim
into its instruction** (or pass `context_depth`) — it forks, so it cannot see the
conversation the ask was made in, and it will refuse rather than guess. The full
lens map is `mj:context/bench.md` (on demand).
