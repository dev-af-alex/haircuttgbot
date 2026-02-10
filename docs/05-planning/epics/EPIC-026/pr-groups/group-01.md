# EPIC-026 — PR Group 01

Status: DONE

## Goal

Establish grouped booking domain and callback contract baseline before wiring end-to-end client flow.

## Included Tasks

- T-001
- T-002
- T-003

## Planned Changes

- Accept ADR for grouped-booking ownership/participant model.
- Introduce schema/domain primitives for grouped request and participant linkage.
- Define callback actions/context for participant progression with stale-safe behavior.
- Keep existing single-booking flow compatible and docker-compose local run stable.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_booking.py tests/test_telegram_callbacks.py tests/test_idempotency.py`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable as backward-compatible domain/contract layer.
- No runtime topology changes; local compose path remains unchanged.

## Completion

- T-001: DONE
- T-002: DONE
- T-003: DONE
