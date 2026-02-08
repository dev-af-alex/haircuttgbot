# EPIC-002 / PR Group 01

Status: DONE

## Objective

Introduce migration framework and first schema cut for core booking entities.

## Included tasks

- T-001 — Add migration toolchain and bootstrap migration
- T-002 — Define core schema entities and constraints

## Why this grouping

- Establishes database contract needed by all product flows.
- Keeps PR mergeable by focusing on schema baseline before seed/CI follow-ups.

## Acceptance checks

- Migration tooling is configured and runnable against local Postgres.
- Initial schema tables and constraints are created through migrations.
- Conflicting booking slot for one master is prevented by DB-level constraint.

## Merge readiness gates

- Local compose path remains healthy after schema initialization.
- Schema changes are documented in architecture docs.
- No secrets or generated junk committed.

## Task status

- T-001: DONE
- T-002: DONE
