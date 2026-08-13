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
