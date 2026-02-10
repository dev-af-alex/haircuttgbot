# EPIC-021 — PR Group 02

Status: DONE

## Goal

Integrate business-timezone semantics into booking/schedule domain logic and Telegram flows while preserving existing functional rules.

## Included Tasks

- T-004
- T-005
- T-006

## Planned Changes

- Apply timezone-aware same-day and business-date calculations in booking/availability.
- Align schedule/day-off/lunch/manual booking logic with business timezone boundaries.
- Ensure Telegram readable date/time outputs and callback paths reflect configured timezone.
- Preserve UTC persistence and idempotent behavior.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_booking.py tests/test_telegram_client_callbacks.py tests/test_telegram_master_callbacks.py`
- `docker compose up -d --build`
- `curl -fsS http://127.0.0.1:8080/health`
- `curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_service_health|bot_api_booking_outcomes_total'`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable after Group 01 timezone baseline.
- Keeps compose path runnable while switching domain behavior to business timezone semantics.
