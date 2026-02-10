# EPIC-023 — PR Group 01

Status: DONE

## Goal

Define reminder policy and introduce durable reminder data contracts so scheduling/dispatch work can be merged safely in later groups.

## Included Tasks

- T-001
- T-002
- T-003

## Planned Changes

- Finalize ADR for reminder timing eligibility and idempotency boundary.
- Add reminder persistence model/migration for due-time and delivery state tracking.
- Implement deterministic eligibility calculation for >=2-hour lead-time rule in business timezone.
- Preserve existing compose startup and booking/cancel baseline behavior.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_booking.py tests/test_timezone.py tests/test_idempotency.py`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `docker compose ps -a`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable independently and should land before scheduler/dispatcher runtime work.
- Keeps docker-compose local run path stable while adding reminder domain/storage primitives.
