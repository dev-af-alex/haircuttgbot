# EPIC-004 / PR Group 01

Status: DONE

## Objective

Introduce mergeable booking-read baseline: service-option contract and availability calculation that excludes blocked intervals.

## Included tasks

- T-001 — Add booking service options contract
- T-002 — Implement availability slot generation service
- T-003 — Exclude blocked times from availability

## Why this grouping

- Delivers a testable read-only slice before write-path risks.
- Keeps local runtime healthy without requiring full Telegram booking state machine yet.
- Unblocks later booking creation work with stable availability contract.

## Acceptance checks

- Availability API/service returns only valid 60-minute slots in 10:00-21:00 window.
- Occupied/day-off/lunch intervals are excluded from candidate slots.
- Service option contract is stable and documented for handler integration.
- `docker compose up -d --build` + current smoke remain passing.

## Merge readiness gates

- Existing CI checks remain green (`pytest`, Bandit, pip-audit, Gitleaks, migration regression).
- Added tests cover slot overlap edge cases.
- Docs updated where interfaces or constraints changed.
- Merge method remains merge-commit.

## Task status

- T-001: DONE
- T-002: DONE
- T-003: DONE
