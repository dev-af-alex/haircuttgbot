# EPIC-021 — PR Group 03

Status: DONE

## Goal

Close EPIC-021 with timezone-focused regressions and synchronized delivery runbooks for local and VM environments.

## Included Tasks

- T-007
- T-008
- T-009

## Planned Changes

- Add regression matrix for business timezone behavior and UTC conversion boundaries.
- Add DST-sensitive test coverage for non-Moscow zone to validate generic correctness.
- Update `docs/04-delivery/local-dev.md` and `docs/04-delivery/deploy-vm.md` with timezone config/smoke checks.
- Perform final doc-sync and merge-gate readiness checks.

## Acceptance Checks

- `.venv/bin/pytest -q`
- `docker compose up -d --build`
- `docker compose ps -a`
- `curl -fsS http://127.0.0.1:8080/health`
- `curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_service_health|bot_api_requests_total|bot_api_request_latency_seconds|bot_api_booking_outcomes_total|bot_api_master_admin_outcomes_total|bot_api_abuse_outcomes_total|bot_api_telegram_delivery_outcomes_total'`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable after Groups 01-02 and focused on quality/doc closure.
- Keeps canonical local run path executable and release-ready with timezone config.
