# EPIC-005 / PR Group 02

Status: DONE

## Objective

Deliver master-initiated cancellation path with mandatory textual reason, ownership guardrails, and reason-aware notifications.

## Included tasks

- T-004 — Implement master cancel flow with mandatory reason
- T-005 — Deliver reasoned cancellation notifications

## Why this grouping

- Builds on Group 01 cancellation contract without introducing smoke/doc closure scope yet.
- Ships master-specific authorization and validation as an isolated write-path slice.
- Keeps local docker-compose behavior stable while adding role-specific cancellation semantics.

## Acceptance checks

- Master cancellation without reason is rejected.
- Master can cancel only bookings tied to their own master profile.
- Client notification for master-initiated cancellation includes reason.
- `docker compose up -d --build` + smoke path remain passing.

## Merge readiness gates

- CI remains green (`pytest`, Bandit, pip-audit, Gitleaks, migration checks).
- Tests cover reason validation, ownership checks, and notification payload content.
- Docs are updated for any API contract/behavior changes.
- Merge method remains merge-commit.

## Task status

- T-004: DONE
- T-005: DONE
