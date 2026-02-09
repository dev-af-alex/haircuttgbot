# EPIC-007 — Observability + reliability baseline

Status: IN_PROGRESS

## Goal

Add an operations baseline for single-VM production: structured logs, metrics, alerts, and a validated PostgreSQL backup/restore runbook.

## Scope

- Structured JSON logging for booking/security lifecycle events with secret-safe payload rules.
- Prometheus metrics endpoint with health, request latency, and booking outcome counters.
- Minimal alert baseline for service health and booking failure spikes.
- Backup and restore runbook for PostgreSQL with local rehearsal evidence.

## Out of scope

- Full production monitoring stack (Grafana/Loki provisioning) beyond local validation.
- Multi-node/high-availability deployment patterns.
- VM rollout packaging and rollback bundle details (EPIC-008).

## Acceptance criteria

- Structured logs include booking lifecycle and RBAC-deny events without token/secret leakage.
- `/metrics` exposes health, request latency, and booking success/failure counters.
- Backup + restore procedure is documented and validated in local rehearsal.
- Local smoke path remains executable with `docker compose up -d --build`.

## Dependencies

- EPIC-001 runtime/CI baseline.
- EPIC-004 booking flow baseline.
- EPIC-006 schedule-management baseline.

## Deliverables

- Logging and metrics instrumentation in `bot-api`.
- Operational runbook updates in delivery docs.
- Rehearsal steps and verification outputs for backup/restore.
- Updated epic planning artifacts (tasks + PR groups).

## Planned PR groups

- Group 01: structured logs + Prometheus metrics baseline.
- Group 02: PostgreSQL backup/restore runbook + rehearsal commands.
- Group 03: alert baseline + smoke/doc sync + closure checks.

## Group 01 observability contract

- Structured event envelope: `event`, `service`, `ts` (ISO-8601 UTC).
- Mandatory security event: `rbac_deny` with actor and command context.
- Booking/schedule lifecycle events emit only operational identifiers/outcomes; raw secrets are forbidden.
- Redaction policy masks keys containing `token`, `secret`, `password`, `authorization`, `api_key`, `database_url` and masks raw `TELEGRAM_BOT_TOKEN` values in string fields.

## Delivered (Group 01)

- Added structured event logging for startup, RBAC-deny, booking lifecycle, and master schedule-write actions.
- Added `/metrics` endpoint with health gauge, request count/latency histogram, and booking/schedule outcome counters.
- Added regression tests for log redaction and metric updates after booking requests.

## Delivered (Group 02)

- Added PostgreSQL backup/restore runbook at `docs/04-delivery/postgresql-backup-restore.md` with prerequisites, dump command, retention, and restore sequence.
- Added clean-state restore rehearsal and integrity-check queries for `users`, `masters`, `bookings`, and `availability_blocks`.
- Updated local-dev runbook to include backup/restore rehearsal in release validation.
