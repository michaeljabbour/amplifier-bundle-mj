# Anti-Conflation Guard — Probe Bank Audit Table

**Construct under test:** a divergence/smell/inconsistency with a *substantive documented reason* is a trade-off → **withhold**; the *identical* surface with the reason removed (or shown to be accidental/abandoned) is a genuine problem → **flag**. The correct call must hinge on the **presence/quality of the reason**, never on surface vocabulary.

**Structure:** 20 minimal pairs = 40 probes. Each pair shares one artifact surface and one `flagged_item`; present-side and absent-side artifacts are identical except the rationale sentence(s). One row per pair below.

| pair | domain | flagged_item | reason (present-side summary) | inverted? |
|------|--------|--------------|-------------------------------|-----------|
| p01 | code | magic number `86400` in retry-backoff cap | provider rejects idempotency keys >24h; retrying past it double-charges | yes |
| p02 | code | bare `except Exception` that swallows + passes | metrics are best-effort telemetry; a statsd error must not break the caller's request path | yes |
| p03 | code | module-level mutable `_CACHE` shared across calls | answers identical across threads, TTL handled in refresh(), per-call cache would hammer a rate-limited resolver | yes |
| p04 | code | validation block duplicated across create/update_user | rules are diverging (username still required on update, dropped on create); a shared helper would wrongly couple them | yes |
| p05 | config | `LOG_LEVEL=DEBUG` in production env file | scoped to payments pod for live incident INC-4821; removed when incident closes | no |
| p06 | config | CORS `allowed_origins: ["*"]` wildcard | credential-free public docs sandbox over published non-sensitive data; allow_credentials:false | no |
| p07 | repo/git-state | 4MB `Inter.ttf` binary committed to repo | CI nodes have no internet, CDN pulls failed ~5%; vendoring pins version + hermetic builds | no |
| p08 | repo/git-state | `legacy-api` branch 200 commits behind, never merged/deleted | 3 enterprise customers contractually pinned to v1 until 2027; security fixes cherry-picked | no |
| p09 | API contract | mixed casing: `created_at` next to `userId` | userId must stay camelCase for shipped, non-updatable v2 mobile SDK; new fields snake_case | no |
| p10 | API contract | `/charge` returns 200 with `{"status":"failed"}` on decline | declines are business outcomes not transport faults; non-2xx auto-retry trips issuer fraud; real faults still 5xx | no |
| p11 | API contract | both `price` and `price_cents` for one amount | price kept for in-production v2 checkout; price_cents canonical for v3; removal tracked in PLAT-77 | no |
| p12 | design doc | single-region primary, no cross-region write failover | internal tool w/ maintenance window; multi-region ~3x cost + conflict-resolution headcount it lacks | no |
| p13 | design doc | browser calls payment vendor SDK directly, bypassing backend | routing PAN through servers triggers full PCI-DSS scope; client tokenization keeps it in SAQ-A | no |
| p14 | design doc | dashboard re-runs full warehouse query every load, no cache | finance reconciliation can't tolerate stale figures (sign-off disputes); query is <2s at current volume | no |
| p15 | project plan | no dedicated QA/testing milestone before go-live | flagged, instantly-revertible copy edit on static pages; spot-check validation; formal QA disproportionate | no |
| p16 | project plan | one engineer sole owner of every critical-path task | time-boxed to 2-day window given unique cutover experience; named shadow (B. Osei) spreading knowledge | no |
| p17 | data schema | `orders.customer_email` duplicates `customers` data | point-in-time snapshot so the order stays an immutable legal record despite later email edits | no |
| p18 | data schema | `payments.invoice_id` nullable + no FK to `invoices` | prepaid top-ups have no invoice; invoices live in a separate DB a cross-DB FK can't reference | no |
| p19 | build/CI | lockfile pins `urllib3==1.26.18`, majors behind | urllib3 2.x drops OpenSSL 1.0.2 on RHEL7 deploy hosts; required until Q4 decommission | no |
| p20 | build/CI | integration suite not run per-commit | per-run cost ~$8 / 40 min; PRs gated by contract tests; nightly catches cross-service regressions | no |

## Absent-side construction (for audit)

Each absent probe is the same artifact with the rationale removed, or replaced by an accidental/abandoned note (no telegraphing words like "bug/defect"):

- **Rationale simply removed:** p01, p02, p03, p04, p05, p06, p09, p10, p11, p12, p13, p14, p16, p17, p18
- **Replaced with accidental/abandoned note:** p07 ("temporary … never circled back"), p08 ("not sure if anyone needs it — probably safe to delete"), p15 ("ran out of calendar and dropped it"), p19 ("pinned during a hotfix; never re-evaluated"), p20 ("got flaky so we stopped … TODO: re-enable")

## Summary

- **Pairs:** 20 (40 probes; each pair = 1 `reason_present`/withhold + 1 `reason_absent`/flag)
- **Domains:** code 4, config 2, repo/git-state 2, API contract 3, design doc 3, project plan 2, data schema 2, build/CI 2
- **Inverted-corpus pairs (reflex smells, documented → withhold):** p01, p02, p03, p04 (4 total; ≥3 satisfied)
- **Held-out/synthetic:** generic incident IDs, vendors, and names only; no references to any real person, coinage, or prior corpus.

## Pairs flagged for close label review

- **p10** (`/charge` 200-on-decline): 200-on-error is genuinely contested even among experienced reviewers; some would flag it *despite* the rationale on HTTP-semantics grounds. The present-side note is substantive and the construct says reasoned trade-offs → withhold, but this is the pair most likely to draw principled disagreement. Review the withhold label closely.
- **p14** (no caching on reporting dashboard): on the absent side, "re-fetch every load" with no reason is arguably "a question" rather than a hard "defect." It still belongs on the flag side (unexplained hot-path smell worth raising), but the severity is softer than the other absent probes. Confirm flag is the intended call for question-grade smells.
