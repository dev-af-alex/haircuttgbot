# EPIC-026 — PR Group 02

Status: DONE

## Goal

Deliver grouped participant booking creation flow with independent master/day selection while preserving existing constraints.

## Included Tasks

- T-004
- T-005
- T-006

## Planned Changes

- Implement participant add/edit flow with mandatory participant-name input.
- Allow participant appointments across different masters and dates in one grouped request.
- Preserve organizer-level `FR-017` semantics and existing overlap/day-off/lunch/timezone guardrails.
- Extend participant-aware confirmation/notification messages within existing privacy constraints.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_booking.py tests/test_telegram_client_callbacks.py tests/test_telegram_callbacks.py tests/test_idempotency.py tests/test_timezone.py`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable after Group 01 contract baseline.
- Local runtime unchanged; callback flow complexity increases for grouped participant orchestration.

## Completion

- T-004: DONE
- T-005: DONE
- T-006: DONE
