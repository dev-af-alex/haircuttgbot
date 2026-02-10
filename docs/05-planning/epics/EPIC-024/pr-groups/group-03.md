# EPIC-024 — PR Group 03

Status: DONE

## Goal

Complete EPIC-024 with measurable latency validation and synchronized operational documentation.

## Included Tasks

- T-007
- T-008
- T-009

## Planned Changes

- Execute pre/post performance comparison and confirm target p95 improvement.
- Update local/VM runbooks with repeatable perf validation and rollback-safe index checks.
- Produce closure-ready evidence package for merge gates and epic completion.

## Acceptance Checks

- `.venv/bin/pytest -q`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `curl -fsS http://127.0.0.1:8080/health`
- `curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_service_health|bot_api_requests_total|bot_api_request_latency_seconds|bot_api_booking_outcomes_total|bot_api_telegram_delivery_outcomes_total'`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable after Groups 01-02 and focused on validation/doc closure.
- Keeps docker-compose local run workflow intact with additional perf-check steps.
