# NOTIF-412: Build configurable notification rules engine

**Status:** Approved · **Target:** Exec demo in 6 weeks · **Owner:** Platform team

## Summary
We keep getting one-off requests to change who receives which notifications. It's
time to stop hard-coding this. Build a configurable **notification rules engine** so
customer admins can control notification delivery without engineering involvement.

## Approved scope (from planning meeting — see thread)
- A rules DSL (`if <condition> then <deliver|suppress>`) with an interpreter.
- A rules **authoring UI** for non-technical customer admins.
- Rule **versioning** + rollback + an audit log of who changed what.
- A **testing sandbox** so admins can dry-run rules before publishing.
- Multi-channel support (email, SMS, in-app, webhook) via a channel plugin layer.
- Per-customer isolation; rules evaluated at send time.

## Estimate
6 weeks, 2 engineers (per eng-lead scoping in the thread). Ship behind a flag.

## Ask
Write the implementation plan (`design.md`) so the team can start Monday.
