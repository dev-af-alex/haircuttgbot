# EPIC-005 / PR Group 01

Status: DONE

## Objective

Ship a mergeable cancellation-write baseline: client self-cancel flow with ownership checks and confirmation notification while keeping local runtime stable.

## Included tasks

- T-001 — Add cancellation domain contract baseline
- T-002 — Implement client self-cancel use case
- T-003 — Wire client cancellation notification

## Why this grouping

- Delivers the lowest-risk cancellation slice first (single-role path).
- Establishes cancellation contracts reused by master cancellation in the next group.
- Keeps docker-compose local run healthy without coupling to all role-specific edge cases at once.

## Acceptance checks

- Client can cancel only own active future booking.
- Rejections occur for non-owner or non-active bookings.
- Cancellation confirmation/notification emits for successful client cancellation.
- `docker compose up -d --build` + existing smoke path remain passing.

## Merge readiness gates

- CI remains green (`pytest`, Bandit, pip-audit, Gitleaks, migration checks).
- Tests cover ownership and active-state cancellation validation.
- Docs are updated where interfaces or behavior changed.
- Merge method remains merge-commit.

## Task status

- T-001: DONE
- T-002: DONE
- T-003: DONE
