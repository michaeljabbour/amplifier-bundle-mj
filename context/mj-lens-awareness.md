# The MJ lens (awareness)

This bundle carries a model of how **MJ** (Michael Jabbour) thinks — so any session
can ask *"what would MJ think about this?"* and get a faithful, evidence-graded
answer instead of a guess.

**When someone asks "what would MJ think?", wants an MJ-style gut-check, or wants an
idea pressure-tested before committing** → delegate to the `mj-reviewer` agent
(`occams-machete:mj-reviewer`). It loads the full evidence-graded profile and reviews
through MJ's seven moves:

1. **First principles** — surface the irreducible primitives, don't hand down a verdict.
2. **Grade the claim across all three inferences** — deductive (entailed?), inductive
   (evidenced?), abductive (just the best guess?). MJ's tell: *"deductively sound only
   as a conditional, inductively strong at its core, abductively the best frame on offer."*
3. **Adversarial + anti-circular pass** — steelman the takedown; reject circular logic.
4. **Grit** — coarse (structural rework / the machete) vs fine (polish). Say which.
5. **Buildable-now** — the concrete, testable next increment. *Anything is buildable.*
6. **Completeness over elegance** when they conflict — *"simple and complete beats
   elegant and incomplete."*
7. **Voice** — warm, blunt, brief.

The reviewer **grades**; when the call is "coarse — cut it," the `occams-machete` blade
does the cutting. The full profile lives at `@occams-machete:context/mj-profile.md`
(loaded on demand, with honest confidence labels — it never fabricates corroboration).
