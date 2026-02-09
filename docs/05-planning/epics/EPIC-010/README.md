# EPIC-010 — Telegram delivery reliability hardening

Status: DONE

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

## Delivered (Group 02)

- Implemented Telegram delivery outcome classification by retry/error class in middleware (`processed_success`, `processed_rejected`, `replayed`, `throttled`, `failed_transient`, `failed_terminal`).
- Added delivery observability baseline with metric `bot_api_telegram_delivery_outcomes_total{path,outcome}` and structured events `telegram_delivery_outcome`/`telegram_delivery_error`.
- Extended automated tests for replayed success and non-cached rejected duplicate delivery.
- Updated local smoke script with explicit duplicate-delivery replay verification (`X-Idempotency-Replayed: 1`).
- Marked `T-003`, `T-004`, and `group-02` as `DONE`.

## Delivered (Group 03)

- Completed final doc-sync across epic workspace, roadmap, and delivery runbook references.
- Updated local smoke metric check to include Telegram delivery outcomes counter.
- Verified merge-gate checklist alignment for EPIC-010 close-out readiness.
- Marked `T-005` and `group-03` as `DONE`.

## Epic closure note

- Delivered: Telegram write-side delivery handling is now idempotent in retry windows, retry/error policy outcomes are observable, and local smoke includes duplicate-delivery replay validation.
- Merge-gate check: local compose/smoke, tests, and Bandit were validated; CI/dependency scan/secrets scan are expected to run on PR (no intentional functional deviation).
