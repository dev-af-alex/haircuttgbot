# EPIC-004 / PR Group 02

Status: DONE

## Objective

Implement booking write-path with transactional validation, including one active future booking limit per client.

## Included tasks

- T-004 — Add client booking creation use case
- T-005 — Enforce one active future booking per client

## Why this grouping

- Adds core booking creation behavior while reusing Group 01 availability/service-option contracts.
- Keeps change mergeable before Telegram handler orchestration in Group 03.
- Isolates write-path validation and concurrency checks in one focused PR.

## Acceptance checks

- Booking create path persists valid booking with selected service option.
- Conflicting active booking interval for the same master is rejected.
- Second active future booking for same client is rejected.
- Existing local run/smoke baseline remains working.

## Merge readiness gates

- CI checks remain green (`pytest`, Bandit, pip-audit, Gitleaks, migration regression).
- Added tests cover conflict and one-active-future-booking rules.
- API/docs are synchronized with new booking endpoint behavior.
- Merge method remains merge-commit.

## Task status

- T-004: DONE
- T-005: DONE
