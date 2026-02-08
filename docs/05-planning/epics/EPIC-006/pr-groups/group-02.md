# EPIC-006 / PR Group 02

Status: DONE

## Objective

Deliver lunch-break update flow for masters and enforce updated lunch boundaries in availability and booking validation.

## Included tasks

- T-004 — Implement lunch break update flow
- T-005 — Apply lunch update to booking/availability validation

## Why this grouping

- Reuses established ownership contracts from Group 01.
- Adds one schedule dimension (lunch) without coupling to manual-booking write path yet.
- Keeps docker-compose runtime stable while tightening conflict semantics.

## Acceptance checks

- Master can update lunch break for own profile.
- Invalid lunch interval/duration/work-window requests are rejected.
- Availability and booking checks enforce updated lunch interval.
- `docker compose up -d --build` + existing smoke remain passing.

## Merge readiness gates

- CI remains green (`pytest`, Bandit, pip-audit, Gitleaks, migration checks).
- Tests cover lunch validation and updated conflict behavior.
- Docs updated where API/behavior changed.
- Merge method remains merge-commit.

## Task status

- T-004: DONE
- T-005: DONE
