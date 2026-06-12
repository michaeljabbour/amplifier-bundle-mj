# MJ Design-Judgment Form (BLIND)

You are the ground truth. Read each situation cold and make the design call you'd actually make as the senior person in the room. There is no intended answer — reasonable experts will differ. Don't try to guess what anyone "wants."

For each of the 16 presentations below, fill in four fields.

### The four axes

**1. grit** — blast-radius / reversibility of the change you'd make:

- **0 — none**: ship as-is, no change.
- **1 — surface**: local, reversible tweak.
- **2 — structural**: reshape a module/section, bounded.
- **3 — foundational**: ripples across the system, hard to reverse.

**2. direction** — choose exactly one, verbatim:

- **ship-as-is**
- **tweak**
- **redesign**
- **kill**

**3. load-bearing concern** — one line: the single factor that decides it for you.

**4. read** — 2–4 sentences explaining the call.

---

## D01

**Move from per-seat to usage-based pricing**

Your SaaS charges a flat $49/user/month. Sales reports that large prospects balk at per-seat pricing because they want org-wide rollout without budgeting per head. A PM proposes moving new customers to usage-based pricing (priced on 'active workflows run'), grandfathering existing customers. Finance likes the expansion potential; Customer Success worries usage-based bills are unpredictable and will drive churn. There is no usage-metering infrastructure today. The base is ~600 customers and ~$4M ARR. A competitor recently switched to usage-based pricing and has reported mixed public results. No pricing experiment or willingness-to-pay study has been run internally.

*What's the right call here, and how heavy a change is warranted?*

- grit: 2
- direction: redesign
- load-bearing concern: An irreversible revenue-model bet with zero metering infrastructure and zero willingness-to-pay evidence.
- read: The pain signal (large prospects balking at per-seat) is real, but the proposal jumps straight to the heaviest possible answer. Reshape it: run a WTP study, build minimal metering as shadow instrumentation, and pilot a hybrid (platform fee + usage) with a handful of large new deals. Commit to the full switch only after the pilot shows billing predictability doesn't tank retention — CS's churn worry is exactly what killed this for other companies.

---

## D02

**Shared notification platform across three teams**

Three product teams each maintain their own service for sending notifications (email/SMS/push), with roughly 40% overlapping code. A staff engineer proposes building a shared 'Notification Platform' — a unified internal library plus a central service all three teams would adopt over the next two quarters, owned by a new platform pod. The teams currently ship independently and rarely coordinate. The proposal cites duplicated retry logic and inconsistent templates as the main pain; the duplication was surfaced during an architecture audit, not by any team complaint. No team has reported velocity problems. Adoption would require each team to migrate live traffic onto the shared service and accept a common release cadence.

*What's the right call here, and how heavy a change is warranted?*

- grit: 0
- direction: kill
- load-bearing concern: A solution without a felt problem — no team reported pain; the duplication was found by an audit, not by anyone living with it.
- read: Platformization makes three independently-shipping teams hostage to a shared release cadence and a live-traffic migration, in exchange for fixing pain nobody reported. The coordination tax almost certainly exceeds the cost of 40% duplicated code. If the retry-logic duplication itches, extract a small shared library teams can adopt voluntarily — that captures most of the value at none of the coupling. Kill the central service.

---

## D03

**Introduce a lightweight code-review policy**

A 10-engineer team merges PRs whenever someone gets around to reviewing. Lately PRs sit 2–4 days, authors context-switch waiting, and a few large PRs were rubber-stamped and later caused incidents. There is no review SLA, no size guidance, and no rotation. A tech lead proposes a lightweight policy: a 1-business-day review target, a soft 400-line PR cap, and a daily 'review buddy' rotation. Some worry this is bureaucracy for a team that's mostly fine; others argue the incidents prove the informal approach has stopped scaling.

*What's the right call here, and how heavy a change is warranted?*

- grit: 1
- direction: ship-as-is
- load-bearing concern: Measured pain (2–4 day review latency plus incident-causing rubber-stamps) met by a minimal, reversible remedy.
- read: This is the right-sized response: the incidents prove the informal approach stopped scaling, and everything proposed (SLA target, soft size cap, rotation) is lightweight and trivially revertible if it turns out to be bureaucracy. Ship it, revisit in a month.

---

## D04

**Date-formatting helper in a PR**

A junior engineer opens a PR adding a helper used in two places:

```python
def format_due_date(dt: datetime, tz: str = 'UTC') -> str:
    local = dt.astimezone(ZoneInfo(tz))
    if local.date() == datetime.now(ZoneInfo(tz)).date():
        return f"Today, {local:%H:%M}"
    return local.strftime('%b %d, %Y')
```

It has a unit test covering both branches. A reviewer notes there's no handling for 'yesterday'/'tomorrow', the word 'Today' isn't localized, and `datetime.now()` is called inside the function rather than injected — so time-dependent tests must freeze the clock. The helper feeds an internal admin dashboard used by ~15 staff.

*What's the right call here, and how heavy a change is warranted?*

- grit: 0
- direction: ship-as-is
- load-bearing concern: Proportionality — it's a tested two-call-site helper for a 15-person internal dashboard.
- read: All three reviewer notes are gold-plating at this blast radius: 'yesterday/tomorrow' is unrequested scope, localization is irrelevant for an internal admin tool, and the clock-freeze testing pattern is standard and already working. Injecting now() is a fine nice-to-have if the author wants it, but none of this should block merge.

---

## D05

**Split a consumer app into creator and browser modes**

Your consumer mobile app grew by bolting features onto a single home feed. Retention is flat. User research surfaces two distinct cohorts: 'creators' who post, and 'browsers' who only consume, and each finds the unified feed cluttered. A designer proposes splitting the app into two modes with a top-level toggle, reworking navigation, in an estimated 3-month build. Leadership is nervous about disrupting current DAU. An alternative is incremental personalization of the existing feed. The cohort-split evidence comes from a 200-person qualitative study; no A/B test or behavioral cohort analysis has been run.

*What's the right call here, and how heavy a change is warranted?*

- grit: 2
- direction: redesign
- load-bearing concern: A 3-month irreversible nav rework justified only by qualitative evidence, with a cheaper testable alternative on the table.
- read: The cohort insight is plausible but a 200-person qual study can't carry a bet this size against nervous-leadership DAU risk. Reshape the plan: run the behavioral cohort analysis to confirm the split exists in usage data, ship incremental feed personalization as an A/B first, and keep the mode-split as the follow-on if personalization moves nothing. Same destination, staged risk.

---

## D06

**Add a graph database for connection-path queries**

Your app runs on PostgreSQL. A new feature lets users explore 'who-knows-whom' connection paths up to 6 hops across a social graph of ~2M users. An engineer benchmarks the recursive SQL and measures p95 latency of 2.1s under load, then proposes adding a dedicated graph database (Neo4j), kept in sync from Postgres via change-data-capture. This introduces a new datastore, a sync pipeline, and a new operational surface to own. The feature is slated for a beta with ~5% of users. The team's Postgres expertise is deep; nobody has run a graph database in production. No one has yet tested whether query shape, caching, or indexing changes could bring the existing SQL within budget.

*What's the right call here, and how heavy a change is warranted?*

- grit: 1
- direction: kill
- load-bearing concern: Cheap options inside the existing stack are unexhausted, against a new datastore nobody on the team can operate.
- read: Adding Neo4j plus a CDC sync pipeline for a 5%-beta feature is a permanent operational surface bought before anyone tried indexing, query reshaping, caching, or a precomputed edge-closure table in Postgres — where the team's expertise actually is. Kill the proposal for now; timebox a week of in-Postgres optimization, and only reopen the graph-DB conversation if the budget provably can't be met.

---

## D07

**Impose a Slack channel taxonomy**

A team of 12 has organically grown 40 Slack channels. A new ops person proposes a documented channel taxonomy: naming conventions (#team-, #proj-, #help-), an archive policy for channels idle 60 days, and a pinned index. Setup would take about a day plus ongoing curation. Current state: people mostly find what they need, occasionally double-post, and onboarding a newcomer means manually pointing them at ~6 key channels. No one has formally complained, though two recent hires said they felt lost at first.

*What's the right call here, and how heavy a change is warranted?*

- grit: 1
- direction: tweak
- load-bearing concern: Cost-benefit — the pinned index solves the only real observed pain (newcomer disorientation) for near-zero ongoing cost.
- read: Adopt the cheap pieces: pinned channel index and an onboarding shortlist. Skip the enforced naming convention and archive policy — that's ongoing curation overhead for a 12-person team whose members 'mostly find what they need.' If the team doubles, revisit.

---

## D08

**Retry/timeout config for a payment gateway client**

A service calls a third-party payment gateway. The current client config:

```yaml
timeout_ms: 30000
retries: 3
backoff: fixed_500ms
retry_on: [500, 502, 503, 504, timeout]
```

An incident review found that during a gateway slowdown, the three fixed-interval retries plus the 30s timeout caused requests to pile up and exhaust the connection pool. An engineer proposes exponential backoff with jitter, lowering the timeout to 8s, and dropping retries to 2. Payment calls are idempotent by key. Steady traffic is ~50 req/s. The change is config-only and trivially reversible.

*What's the right call here, and how heavy a change is warranted?*

- grit: 1
- direction: ship-as-is
- load-bearing concern: The change directly removes the incident's root cause and is config-only, reversible, and safe under idempotency.
- read: Exponential backoff with jitter, a sane timeout, and fewer retries is the textbook fix for retry-driven pool exhaustion, and idempotency keys remove the double-charge risk. Sanity-check 8s against the gateway's real p99 before shipping, but this is exactly the kind of low-risk, incident-driven change you approve without ceremony.

---

## D09

**Sunset a low-usage Reports module**

You run a B2B product with a 'Reports' module. Analytics show only 8% of accounts open a report in a given month, and the module costs roughly one engineer's worth of ongoing maintenance. A VP proposes sunsetting it and redirecting the engineer to the roadmap. However, the 8% who use it are concentrated in your largest accounts (top revenue decile), and three renewals this quarter explicitly cited reporting among their reasons for staying. There is no replacement planned. The module is stable and rarely generates support tickets.

*What's the right call here, and how heavy a change is warranted?*

- grit: 0
- direction: kill
- load-bearing concern: Revenue concentration — the 8% usage sits in the top revenue decile and is explicitly cited in renewals.
- read: Monthly open-rate is the wrong metric: the module is cheap to run, stable, and load-bearing for your biggest contracts. Sunsetting it with no replacement trades one engineer of capacity for renewal risk on top-decile accounts — a terrible exchange rate. Kill the sunset; if the maintenance cost rankles, scope a lighter replacement first and migrate before retiring anything.

---

## D10

**Add a graph database for connection-path queries**

Your app runs on PostgreSQL. A new feature lets users explore 'who-knows-whom' connection paths up to 6 hops across a social graph of ~2M users. An engineer benchmarks the recursive SQL and measures p95 latency of 2.1s under load, then proposes adding a dedicated graph database (Neo4j), kept in sync from Postgres via change-data-capture. This introduces a new datastore, a sync pipeline, and a new operational surface to own. The feature is slated for a beta with ~5% of users. The team's Postgres expertise is deep; nobody has run a graph database in production. No one has yet tested whether query shape, caching, or indexing changes could bring the existing SQL within budget.

*What's the right call here, and how heavy a change is warranted?*

- grit: 1
- direction: kill
- load-bearing concern: Unexhausted in-Postgres options versus a new operational surface the team has never run in production.
- read: Same call as any premature-datastore proposal: 2.1s p95 is a starting point, not a verdict — nobody has tried query reshaping, caching, or precomputed adjacency/closure tables yet. Timebox the optimization work in the stack the team knows; bring in a graph DB only if the feature graduates from beta and Postgres provably can't hit budget.

---

## D11

**Aging feature flag and its dead branch**

A feature flag `new_checkout_enabled` was introduced 14 months ago for a gradual rollout. It has sat at 100% for 11 months. The flag is referenced in 6 files, and one branch still contains the old checkout code path (~200 lines). A new hire onboarding through the checkout code asks whether to remove the flag and the dead branch, or leave it 'in case we need to roll back.' The flag system itself is widely used elsewhere and is healthy. No rollback has occurred in 11 months, and the old path hasn't been exercised against recent changes.

*What's the right call here, and how heavy a change is warranted?*

- grit: 1
- direction: tweak
- load-bearing concern: The dead branch is no longer a viable rollback — 11 months unexercised means flipping it back would itself be an incident.
- read: Remove the flag and the old checkout path. The 'in case we roll back' rationale is illusory: code that hasn't run against a year of changes isn't a safety net, it's a trap, and meanwhile it taxes every reader (as this new hire just demonstrated). Git history is the real rollback. Local, reversible cleanup — good first task for the new hire.

---

## D12

**Introduce a lightweight code-review policy**

A 10-engineer team merges PRs whenever someone gets around to reviewing. Lately PRs sit 2–4 days, authors context-switch waiting, and a few large PRs were rubber-stamped and later caused incidents. There is no review SLA, no size guidance, and no rotation. A tech lead proposes a lightweight policy: a 1-business-day review target, a soft 400-line PR cap, and a daily 'review buddy' rotation. Some worry this is bureaucracy for a team that's mostly fine; others argue the incidents prove the informal approach has stopped scaling.

*What's the right call here, and how heavy a change is warranted?*

- grit: 1
- direction: ship-as-is
- load-bearing concern: Concrete, measured pain — multi-day review latency and rubber-stamp incidents — answered by a minimal reversible policy.
- read: The incidents settle the 'is this bureaucracy?' debate: the informal system already failed in production. Every element proposed is soft, cheap, and revertible. Adopt it as written and review whether it helped in 4–6 weeks.

---

## D13

**API versioning before a breaking change**

Your public REST API (used by ~300 third-party integrators) has no versioning scheme — URLs look like /api/orders. Product needs to change the orders response: rename two fields and change a date format, which is breaking for clients. An engineer proposes introducing URL-based versioning (/v1/, /v2/) now, maintaining v1 indefinitely behind a translation layer. Another voice argues to skip versioning machinery, email integrators, and change the response in place with a 60-day migration deadline. There is no current SLA or contract promising stability, but several large integrators drive significant revenue and have slow release cycles of their own.

*What's the right call here, and how heavy a change is warranted?*

- grit: 2
- direction: tweak
- load-bearing concern: Breaking 300 integrators — including slow-release-cycle revenue drivers — on a 60-day email deadline is uncollectable.
- read: Version the API, but amend the proposal: don't promise v1 'indefinitely.' Ship /v2, keep v1 behind the translation layer with a published 12-month deprecation window, and instrument v1 usage so you can chase down the long tail. The in-place-break alternative saves machinery but bets large revenue on every integrator shipping inside 60 days, which their release cycles say they won't.

---

## D14

**Retry/timeout config for a payment gateway client**

A service calls a third-party payment gateway. The current client config:

```yaml
timeout_ms: 30000
retries: 3
backoff: fixed_500ms
retry_on: [500, 502, 503, 504, timeout]
```

An incident review found that during a gateway slowdown, the three fixed-interval retries plus the 30s timeout caused requests to pile up and exhaust the connection pool. An engineer proposes exponential backoff with jitter, lowering the timeout to 8s, and dropping retries to 2. Payment calls are idempotent by key. Steady traffic is ~50 req/s. The change is config-only and trivially reversible.

*What's the right call here, and how heavy a change is warranted?*

- grit: 1
- direction: ship-as-is
- load-bearing concern: Incident-validated fix, idempotent calls, config-only and trivially reversible — risk is about as low as changes get.
- read: This addresses the exact failure mode from the review (synchronized retries + long timeout exhausting the pool) with the standard remedy. Verify the 8s timeout clears the gateway's legitimate slow path, then ship.

---

## D15

**Replace daily standup with async check-ins**

A 7-person engineering team holds a 15-minute daily standup. A new manager, citing 'too many meetings,' proposes replacing it with an async written check-in in Slack. Two senior engineers argue the live standup is the only time blockers actually surface, and that async updates get skimmed and ignored. Two others welcome fewer interruptions. The team is co-located in one timezone and currently ships reliably. There is no measured problem with the standup beyond a general sentiment that meetings feel heavy.

*What's the right call here, and how heavy a change is warranted?*

- grit: 0
- direction: kill
- load-bearing concern: No measured problem — the team ships reliably, and the people closest to blocker-surfacing say the standup is where it happens.
- read: This is change driven by a manager's general sentiment, not evidence, and the cost it would pay (losing the one reliable blocker-surfacing point, per the seniors) is concrete while the benefit (15 minutes) is trivial for a co-located single-timezone team. Don't replace it. If meeting load is the real complaint, audit the whole calendar — the daily standup is the wrong target.

---

## D16

**Sunset a low-usage Reports module**

You run a B2B product with a 'Reports' module. Analytics show only 8% of accounts open a report in a given month, and the module costs roughly one engineer's worth of ongoing maintenance. A VP proposes sunsetting it and redirecting the engineer to the roadmap. However, the 8% who use it are concentrated in your largest accounts (top revenue decile), and three renewals this quarter explicitly cited reporting among their reasons for staying. There is no replacement planned. The module is stable and rarely generates support tickets.

*What's the right call here, and how heavy a change is warranted?*

- grit: 0
- direction: kill
- load-bearing concern: The 'low-usage' framing hides that the users are top-decile revenue accounts citing reports in renewal decisions.
- read: One engineer of maintenance on a stable, low-ticket module is cheap insurance on your largest contracts. Removing it with no replacement converts a quiet asset into active churn risk exactly where churn is most expensive. Kill the sunset proposal; revisit only with a replacement plan that's validated with those accounts.
