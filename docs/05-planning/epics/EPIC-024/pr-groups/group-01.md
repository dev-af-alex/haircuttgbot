# EPIC-024 — PR Group 01

Status: DONE

## Goal

Establish baseline profiling evidence and a fixed optimization decision before changing schema/query behavior.

## Included Tasks

- T-001
- T-002
- T-003

## Planned Changes

- Create and accept ADR for query/index optimization strategy and measurement protocol.
- Capture baseline query plans and timings for critical booking/schedule reads.
- Add repeatable local perf harness/commands for comparing baseline and optimized paths.
- Preserve current docker-compose functional behavior.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_booking.py tests/test_telegram_master_callbacks.py tests/test_timezone.py`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable independently as non-breaking baseline/profiling preparation.
- Keeps local compose run path stable while adding perf measurement contract.
