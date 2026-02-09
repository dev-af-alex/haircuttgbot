# EPIC-016 — PR Group 01

## Objective

Deliver mergeable domain foundation for booking-time guardrails and day-off conflict checks before callback-level behavior changes.

## Scope

- Create ADR stub for same-day booking cutoff and day-off conflict policy.
- Add shared same-day boundary helper used by availability/booking validation layers.
- Add reusable day-off conflict predicate against active bookings on target date.
- Keep existing user-visible booking/master flow behavior unchanged in this group.

## Tasks included

- T-001 Finalize guardrail and day-off conflict policy ADR - DONE.
- T-002 Add shared same-day booking boundary helper - DONE.
- T-003 Add day-off conflict validation primitive - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable independently via merge commit.
- No destructive schema migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0, runtime services healthy).
- Existing smoke path stays green.

## Acceptance checks

1. ADR stub exists and captures pending decision points for cutoff/rounding/conflict semantics.
2. Shared boundary helper deterministically excludes already-passed same-day windows.
3. Day-off conflict primitive returns clear pass/fail result for occupied target dates.
4. Canonical local smoke baseline passes without regressions.

## Validation commands

```bash
docker compose up -d --build
docker compose ps -a
.venv/bin/pytest -q
curl -fsS http://127.0.0.1:8080/health
```

## Group status

Status: DONE
Completed at: 2026-02-09
