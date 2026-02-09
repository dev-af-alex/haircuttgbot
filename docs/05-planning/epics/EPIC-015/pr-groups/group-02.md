# EPIC-015 — PR Group 02

## Objective

Apply readable time formatting and mobile-friendly keyboard layout updates across client interactive booking/cancel flows.

## Scope

- Replace remaining raw or low-context client-facing booking/cancel timestamps with shared `ru` formatter output.
- Improve client booking-step keyboard composition for phone screens while keeping callback contracts intact.
- Keep existing business rules (RBAC, one-active-booking, slot-conflict/idempotency behavior) unchanged.

## Tasks included

- T-004 Apply readable formatting to client booking/cancel messages - DONE.
- T-005 Refactor client interactive keyboards for mobile usability - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable by merge commit independently.
- No schema migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0; runtime services healthy).
- Existing smoke and callback tests remain green.

## Acceptance checks

1. Client booking confirmation and cancellation prompts/results include readable `ru` slot date/time context.
2. Client interactive keyboards (menu/master/service/date/slot/cancel paths) remain phone-usable and callback-safe.
3. Client-flow regression tests cover readable formatting and keyboard row constraints.
4. Canonical smoke baseline from `docs/04-delivery/local-dev.md` passes without regressions.

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
