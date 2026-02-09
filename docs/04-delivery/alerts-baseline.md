# Alert baseline (single VM, EPIC-007 Group 03)

## Scope

Minimal Prometheus alerting baseline for MVP operations:

- service-down detection (`bot-api` unreachable/unhealthy),
- booking/schedule write failure spike detection.

## Rule 1: Bot API down

- Alert name: `BotApiServiceDown`
- Severity: `critical`
- PromQL:
  `bot_api_service_health < 1`
- For: `2m`
- Response notes:
  1. Verify container health: `docker compose ps`
  2. Inspect service logs: `docker compose logs bot-api --tail=200`
  3. Confirm DB/Redis readiness: `docker compose ps postgres redis`
  4. If startup/config issue, recover with: `docker compose up -d --build`

## Rule 2: Booking/schedule failure spike

- Alert name: `BookingFailuresHigh`
- Severity: `warning`
- PromQL:
  `sum(increase(bot_api_booking_outcomes_total{outcome="failure"}[15m])) >= 5`
- For: `15m`
- Response notes:
  1. Check failing actions:
     `curl -fsS http://127.0.0.1:8080/metrics | grep 'bot_api_booking_outcomes_total{action='`
  2. Review recent app events:
     `docker compose logs bot-api --tail=300 | grep -E 'booking_|schedule_|rbac_deny'`
  3. Validate DB availability and lock/contention indicators from postgres logs.
  4. If failures are from expected user validation (not incident), keep as warning and track trend.

## Operational guidance

- Thresholds are intentionally conservative for MVP traffic and should be recalibrated after production baseline data.
- These rules are compatible with Alertmanager-style routing but do not require Grafana/Loki provisioning in this epic.
