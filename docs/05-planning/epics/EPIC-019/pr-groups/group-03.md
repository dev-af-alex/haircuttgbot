# EPIC-019 — PR Group 03

Status: DONE

## Goal

Close EPIC-019 with regression safety net and synchronized local/VM smoke documentation for the new registration/baseline contract.

## Included Tasks

- T-005
- T-006

## Planned Changes

- Add and stabilize regression tests for:
  - bootstrap-only initial user baseline,
  - `/start` auto-registration idempotency,
  - nickname persistence in user records.
- Update `docs/04-delivery/local-dev.md` and `docs/04-delivery/deploy-vm.md` smoke paths to verify:
  - no extra seeded users beyond bootstrap owner,
  - first organic user registration through Telegram `/start`.
- Perform final doc-sync and definition-of-done checks for epic closure readiness.

## Acceptance Checks

- `.venv/bin/pytest -q`
- `docker compose up -d --build`
- `docker compose ps -a`
- `curl -fsS http://127.0.0.1:8080/health`
- `curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_service_health|bot_api_requests_total|bot_api_request_latency_seconds|bot_api_booking_outcomes_total|bot_api_master_admin_outcomes_total|bot_api_abuse_outcomes_total|bot_api_telegram_delivery_outcomes_total'`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable after Groups 01-02 and focused on hardening + doc sync.
- Keeps canonical local run path executable with updated smoke assertions.
