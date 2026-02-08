# ADR-0004: PostgreSQL backup/restore baseline for single VM

Date: 2026-02-08
Status: Proposed
Deciders: Engineering

## Context

EPIC-007 requires a validated backup/restore runbook for single-VM operations. We need a default strategy that is executable with docker-compose, fits MVP operational complexity, and can be rehearsed locally without extra infrastructure.

## Decision

TODO in EPIC-007 implementation. Candidate direction: logical PostgreSQL dumps (`pg_dump`) with scheduled retention and documented restore rehearsal steps.

## Alternatives considered

- Physical volume snapshots only (filesystem-level backup).
- WAL archiving + point-in-time recovery setup.
- Managed external backup service.

## Consequences

Positive, negative, and follow-up actions will be finalized with EPIC-007 Group 02 once rehearsal evidence is collected.
