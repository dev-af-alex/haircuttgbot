# Reliability NFR

## 1) Availability / SLO

- SLO: TODO (target availability for booking flow and schedule management).
- Error budget policy: TODO (allowed downtime/failure and escalation process).

## 2) Recovery objectives

- RTO: <= 60 minutes for full PostgreSQL logical-restore recovery on single VM.
- RPO: <= 24 hours (daily logical backup baseline).

## 3) Backups / DR

- Backups: daily PostgreSQL logical dump (`pg_dump -Fc`) with at least 7 local daily copies and daily off-host copy.
- Restore procedure: tested clean-state restore runbook in `docs/04-delivery/postgresql-backup-restore.md` using `pg_restore --clean --if-exists`.

## 4) Observability

- Logs: structured application and security logs for booking/schedule actions.
- Metrics: baseline implemented for API latency (`bot_api_request_latency_seconds`), request count (`bot_api_requests_total`), health (`bot_api_service_health`), and booking/schedule outcomes (`bot_api_booking_outcomes_total`).
- Traces: TODO (if distributed components added beyond single service).
- Alerts: TODO (service down, DB connectivity issues, high booking error rate).
