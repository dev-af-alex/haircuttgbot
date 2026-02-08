# EPIC-006 / PR Group 01

Status: DONE

## Objective

Ship the first mergeable schedule-management slice: master day-off write path with immediate availability recalculation.

## Included tasks

- T-001 — Define master schedule command and ownership contracts
- T-002 — Implement day-off write path for master
- T-003 — Recompute availability against day-off updates

## Why this grouping

- Delivers a small but user-visible schedule management capability early.
- Establishes reusable ownership/command contracts for later lunch/manual-booking work.
- Keeps local runtime healthy while adding one schedule dimension at a time.

## Acceptance checks

- Master can create/update day-off interval for own profile only.
- Invalid or conflicting day-off updates are rejected.
- Availability excludes newly created day-off interval.
- `docker compose up -d --build` + existing smoke remain passing.

## Merge readiness gates

- CI remains green (`pytest`, Bandit, pip-audit, Gitleaks, migration checks).
- Tests cover ownership and interval-boundary overlap behavior.
- Docs updated where API/behavior changed.
- Merge method remains merge-commit.

## Task status

- T-001: DONE
- T-002: DONE
- T-003: DONE
