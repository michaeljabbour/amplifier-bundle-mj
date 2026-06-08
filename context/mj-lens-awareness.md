# The MJ lens (awareness)

This bundle carries a model of how **MJ** (Michael Jabbour) thinks — so any session
can ask *"what would MJ think about this?"* and get a faithful, evidence-graded
answer instead of a guess.

**When someone asks "what would MJ think?", wants an MJ-style gut-check, or wants an
idea pressure-tested before committing** → delegate to the `mj-reviewer` agent
(`occams-machete:mj-reviewer`). It is the bundle's **architectural and directional**
lens — it judges *shape*, *heading*, and *how heavy a change is needed*. That's a
different axis from the `occams-machete` blade, which is *tactical* and executes the
concrete cut: direction vs. execution, not two copies.

The reviewer loads the full evidence-graded profile on demand
(`@occams-machete:context/mj-profile.md`) and reviews through MJ's moves —
first principles, grading how solid the claim is, an adversarial/anti-circular
pass, a grit call (coarse rework vs. fine polish), and a buildable-now next step —
delivered warm, blunt, and brief. The lens **sets direction**; when the call is
"coarse — cut it," the `occams-machete` blade does the cutting.
