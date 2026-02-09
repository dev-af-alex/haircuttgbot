# ADR-0004: PostgreSQL backup/restore baseline for single VM

Date: 2026-02-08
Status: Accepted
Deciders: Engineering

## Context

EPIC-007 requires a validated backup/restore runbook for single-VM operations. We need a default strategy that is executable with docker-compose, fits MVP operational complexity, and can be rehearsed locally without extra infrastructure.

## Decision

Adopt logical PostgreSQL backups using `pg_dump` in custom format (`-Fc`) as the baseline for single-VM operations.

- Cadence: at least daily backups and before schema migrations.
- Retention: keep minimum 7 daily copies on-host and copy daily backup off-host.
- Restore: use `pg_restore --clean --if-exists` into a recreated clean database.
- Validation: run restore rehearsal and integrity-check queries (`users`, `masters`, `bookings`, `availability_blocks`) following `docs/04-delivery/postgresql-backup-restore.md`.

## Alternatives considered

- Physical volume snapshots only (filesystem-level backup).
- WAL archiving + point-in-time recovery setup.
- Managed external backup service.

## Consequences

- Positive: low operational complexity, reproducible commands for local and VM environments, and explicit recovery validation path.
- Negative: no point-in-time recovery; worst-case data loss window equals backup cadence.
- Follow-up: evaluate WAL/PITR in later hardening if stricter RPO is required.
