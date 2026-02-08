# EPIC-002 — Data model + migration baseline

Status: DONE

## Goal

Implement the initial relational model and migration flow for users/roles, masters, bookings, availability blocks, and audit events.

## Scope

- Migration tooling setup and migration execution in local runtime.
- Initial schema for core entities and constraints.
- Seed data for at least two masters.
- Documentation updates for schema and local migration behavior.

## Out of scope

- Telegram command handlers and business flow orchestration.
- Advanced reporting and analytics schema.

## Acceptance criteria

- Initial schema is managed by migrations and applied automatically in local setup.
- Constraints prevent double-booking for the same master and slot.
- Seed data includes at least two masters for smoke scenarios.
- Documentation reflects schema and migration workflow.

## Dependencies

- EPIC-001 runtime baseline (`bot-api`, `postgres`, `redis`, CI checks).

## Deliverables

- Migration config + migration scripts.
- SQLAlchemy/ORM model baseline (or equivalent).
- Seed script and docs updates.

## Delivered

- Alembic migration baseline with initial schema and booking conflict constraints.
- Automatic migration execution in compose lifecycle via `migrate` one-shot service.
- Idempotent seed script with two master profiles for smoke scenarios.
- CI schema regression check (`alembic upgrade head` on ephemeral Postgres).

## Closure verification (2026-02-08)

- All tasks in `tasks.md` are `DONE`.
- All PR groups are `DONE`.
- PR and doc-sync merge gates are satisfied.
- Intentional deviations: none.
