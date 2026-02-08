# Reliability NFR

## 1) Availability / SLO

- SLO: TODO (target availability for booking flow and schedule management).
- Error budget policy: TODO (allowed downtime/failure and escalation process).

## 2) Recovery objectives

- RTO: TODO (max acceptable restore time after outage).
- RPO: TODO (max acceptable data loss window for bookings/schedule updates).

## 3) Backups / DR

- Backups: TODO (PostgreSQL backup cadence, retention, and storage location on single VM/offsite).
- Restore procedure: TODO (tested runbook for full restore and point-in-time validation).

## 4) Observability

- Logs: structured application and security logs for booking/schedule actions.
- Metrics: TODO (command latency, booking success/failure, webhook processing queue).
- Traces: TODO (if distributed components added beyond single service).
- Alerts: TODO (service down, DB connectivity issues, high booking error rate).
