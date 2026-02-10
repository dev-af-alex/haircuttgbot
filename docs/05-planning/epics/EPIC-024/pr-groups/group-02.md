# EPIC-024 — PR Group 02

Status: DONE

## Goal

Implement performance improvements through migration-backed indexes and minimal query refactors while keeping booking behavior unchanged.

## Included Tasks

- T-004
- T-005
- T-006

## Planned Changes

- Add index migrations for slow-path booking/schedule queries.
- Apply targeted service/query adjustments for planner efficiency when indexes are insufficient.
- Add regression tests for correctness and migration safety.
- Keep timezone, RBAC, and notification behavior intact.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_booking.py tests/test_telegram_callbacks.py tests/test_telegram_master_callbacks.py tests/test_idempotency.py tests/test_timezone.py`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable after Group 01 baseline evidence and ADR alignment.
- Preserves local compose operability while introducing query/index performance changes.
