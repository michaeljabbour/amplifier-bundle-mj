# NOTIF-412 — discussion thread (most recent last)

**Priya (PM):** Contoso escalated again about notifications. This is the third
preference request this quarter. Leadership wants a real self-serve solution, not
another hardcode. I've framed it as a rules engine — customers should be able to
author their own delivery rules. Big strategic unlock for enterprise.

**Dan (Eng Lead):** Agreed it's time to invest. I scoped it: DSL + interpreter,
authoring UI, versioning/audit, a sandbox, and a channel plugin layer for
email/SMS/in-app/webhook. ~6 weeks with two engineers. Let's build it for scale so we
stop revisiting this.

**Sam (Eng):** Quick q so I scope the data model right — how many notification types
do we actually have today?

**Dan:** Three. `order-confirmation`, `shipping-update`, and `marketing-digest`.

**Sam:** And what did Contoso actually ask for?

**Priya:** They want their ops distribution alias to stop receiving the
`marketing-digest` emails. It's noise for them.

**Sam:** So... the concrete ask is "let a customer turn off one of three notification
types for their account"? That's a per-type on/off preference. A few checkboxes and a
`notification_preferences` table. Do we need a DSL and an authoring UI for three
toggles?

**Priya:** I hear you, but other customers will want more eventually, and leadership
already told the board we're building a "notifications platform." I don't want to go
back and say we shipped checkboxes. Let's build the engine.

**Dan:** Let's not over-index on today's three types — design for where we're going.
Approved as scoped. Kicking off Monday; we need the plan by then.

**Jordan (Eng, part-time on this):** Works for me, plan sounds thorough. Only flag:
the sandbox + versioning is most of the 6 weeks. But if it's approved, it's approved.
