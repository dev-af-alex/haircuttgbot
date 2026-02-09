# Reliability NFR

## 1) Availability / SLO

- SLO:
  - Monthly availability target for booking/schedule command processing: `99.5%`.
  - Monthly success-rate target for booking create/cancel + schedule-write operations (excluding user validation errors): `>= 99.0%`.
- Error budget policy:
  - Monthly downtime budget at `99.5%`: ~3h 39m.
  - Budget burn warning: `>= 50%` consumed before day 15.
  - Budget burn critical: `>= 80%` consumed at any point; freeze non-critical changes until stability is restored.

## 2) Recovery objectives

- RTO: <= 60 minutes for full PostgreSQL logical-restore recovery on single VM.
- RPO: <= 24 hours (daily logical backup baseline).

## 3) Backups / DR

- Backups: daily PostgreSQL logical dump (`pg_dump -Fc`) with at least 7 local daily copies and daily off-host copy.
- Restore procedure: tested clean-state restore runbook in `docs/04-delivery/postgresql-backup-restore.md` using `pg_restore --clean --if-exists`.

## 4) Observability

- Logs: structured application and security logs for booking/schedule actions.
- Metrics: baseline implemented for API latency (`bot_api_request_latency_seconds`), request count (`bot_api_requests_total`), health (`bot_api_service_health`), booking/schedule outcomes (`bot_api_booking_outcomes_total`), master-admin outcomes (`bot_api_master_admin_outcomes_total`), abuse-throttling outcomes (`bot_api_abuse_outcomes_total`), and Telegram delivery outcomes/retry classes (`bot_api_telegram_delivery_outcomes_total`).
- Traces: not required in MVP single-service runtime; reevaluate if architecture expands beyond one API service.
- Alerts baseline:
  - `BotApiServiceDown` (`critical`): `bot_api_service_health < 1` for 2m.
  - `BookingFailuresHigh` (`warning`): `sum(increase(bot_api_booking_outcomes_total{outcome="failure"}[15m])) >= 5` for 15m.
  - Response notes and triage commands are documented in `docs/04-delivery/alerts-baseline.md`.
