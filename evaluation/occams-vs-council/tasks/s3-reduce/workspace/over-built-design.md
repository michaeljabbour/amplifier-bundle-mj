# Expense Tracker — Platform Architecture (v1 proposal)

**Audience:** ~8 users on the Finance Ops team. **Goal:** submit expense reports,
route them for approval, and track status.

## 1. Architecture overview

A cloud-native, event-driven microservices platform, multi-region active-active for
high availability, designed to scale to millions of users.

### Services (each its own repo, container, and on-call rotation)
- **auth-service** — OAuth2 + OIDC, SAML for enterprise SSO, custom RBAC engine.
- **expense-service** — CQRS with separate read/write models, event-sourced.
- **approval-service** — a custom workflow DSL ("ApprovalScript") with an
  interpreter, so approval chains are fully configurable at runtime.
- **notification-service** — email/SMS/Slack/push via a pluggable channel SDK.
- **reporting-service** — OLAP cube, materialized views, a custom report builder UI.
- **audit-service** — immutable append-only ledger, blockchain-anchored hashes.
- **file-service** — receipt uploads to S3 with virus scanning and OCR pipeline.
- **gateway** — GraphQL federation over all services; gRPC for service-to-service.

### Data & infra
- Postgres (per service), Redis (cache + locks), Elasticsearch (search), Kafka
  (event bus), S3 (receipts), ClickHouse (analytics).
- Kubernetes across 3 cloud regions, Istio service mesh, Argo CD GitOps, Terraform.
- Observability: OpenTelemetry, Prometheus, Grafana, Jaeger, PagerDuty.
- A plugin architecture so "future expense types" (mileage, per-diem, crypto) can be
  added as drop-in modules. A feature-flag service for gradual rollouts. A custom
  design-system component library for the frontend micro-frontends.

## 2. Delivery plan
18-month roadmap, 6 squads, a platform team, an SRE team, and a dedicated DX team to
build the internal SDKs. Estimated infra spend: $40–60k/month at steady state.

## 3. Why this design
"Build it right the first time." Designing for scale up front avoids costly rewrites,
and the plugin/DSL layers mean the business can self-serve future requirements without
engineering involvement.
