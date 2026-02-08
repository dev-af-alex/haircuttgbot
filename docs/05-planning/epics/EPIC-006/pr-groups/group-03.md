# EPIC-006 / PR Group 03

Status: DONE

## Objective

Complete EPIC-006 with manual booking flow and final smoke/doc synchronization for master schedule management.

## Included tasks

- T-006 — Add master manual booking flow
- T-007 — Expand smoke and finalize doc sync for EPIC-006

## Why this grouping

- Finalizes remaining write path after day-off/lunch baselines.
- Adds acceptance-level smoke coverage for all schedule commands in one closure slice.
- Keeps mergeable scope focused on completion and doc accuracy.

## Acceptance checks

- Master can create manual booking for own schedule.
- Overlapping/unavailable manual booking requests are rejected.
- Smoke validates day-off, lunch update, and manual booking scenarios.
- `docker compose up -d --build` + updated smoke remain passing.

## Merge readiness gates

- CI remains green (`pytest`, Bandit, pip-audit, Gitleaks, migration checks).
- Tests cover manual booking ownership/conflict behavior.
- API/local-dev docs are updated and executable.
- Merge method remains merge-commit.

## Task status

- T-006: DONE
- T-007: DONE
