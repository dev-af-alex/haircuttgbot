# EPIC-010 — Telegram delivery reliability hardening

Status: IN_PROGRESS

## Goal

Harden Telegram integration for webhook retries, idempotent command handling, and controlled failure behavior under external API constraints.

## Scope

- Define and implement duplicate-delivery/idempotency handling for Telegram command paths.
- Formalize retry/error policy for webhook processing and downstream transient failures.
- Add observability for duplicate events and retry outcomes.
- Extend local smoke path with duplicate-delivery validation.

## Out of scope

- Full asynchronous queue platform migration.
- Multi-provider messaging abstraction.
- Major UX/flow redesign for booking/schedule commands.

## Acceptance criteria

- Repeated Telegram deliveries within retry window do not create duplicate write-side effects.
- Retry/error policy is documented with deterministic behavior by failure class.
- Metrics/logs expose duplicate-delivery and retry outcome visibility.
- Local docker-compose run + smoke remain reproducible.

## Dependencies

- EPIC-003 auth + RBAC baseline.
- EPIC-007 observability baseline.
- EPIC-009 abuse protection baseline.

## Deliverables

- Idempotency baseline for Telegram-facing write paths.
- Delivery retry policy contract in architecture/delivery docs.
- Tests + smoke updates for duplicate-delivery scenarios.

## Planned PR groups

- Group 01: delivery/idempotency strategy + ADR + baseline guard implementation.
- Group 02: retry policy implementation + observability contract expansion.
- Group 03: smoke hardening + closure sync.

## Notes

- Every PR group must keep local `docker compose` workflow operational.
- Merge method remains merge-commit per repository policy.

## Delivered (Group 01)

- Finalized idempotency strategy and contract in `docs/90-decisions/adr-0007-telegram-delivery-idempotency-strategy.md`.
- Implemented bounded replay-idempotency guard for Telegram write-side endpoints with deterministic replay response header `X-Idempotency-Replayed: 1`.
- Added automated tests for replay behavior and kept abuse-throttle coverage compatible with idempotency guards.
- Marked `T-001`, `T-002`, and `group-01` as `DONE`.
