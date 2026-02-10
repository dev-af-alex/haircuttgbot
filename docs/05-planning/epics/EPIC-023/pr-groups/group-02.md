# EPIC-023 — PR Group 02

Status: DONE

## Goal

Deliver runnable reminder scheduling and Telegram dispatch integration with idempotent behavior under retries/restarts.

## Included Tasks

- T-004
- T-005
- T-006

## Planned Changes

- Add reminder poller/scheduler worker path to runtime.
- Dispatch reminders via existing Telegram delivery mechanisms with duplicate-send protection.
- Record reminder lifecycle outcomes and expose observability metrics/events.
- Keep RBAC and existing booking/cancel flows unchanged.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_booking.py tests/test_idempotency.py tests/test_observability.py`
- `docker compose up -d --build`
- `curl -fsS http://127.0.0.1:8080/health`
- `curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_booking_outcomes_total|bot_api_telegram_delivery_outcomes_total'`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable after Group 01 reminder contract baseline.
- Keeps canonical local run path working while adding asynchronous reminder processing behavior.
