# EPIC-023 — Time-window reminder notifications (2 hours before appointment)

Status: IN_PROGRESS
Started: 2026-02-10
Roadmap source: `docs/05-planning/epics.md`

## Goal

Add proactive reminder notifications for clients exactly for appointments created more than 2 hours before slot start.

## Scope

- Introduce reminder scheduling and dispatch for upcoming bookings.
- Apply strict eligibility rule: reminders are sent only when booking was created at least 2 hours before slot start.
- Ensure reminder processing is idempotent under retries/restarts and does not duplicate delivery.
- Keep reminder timing based on `BUSINESS_TIMEZONE`, while persistence remains UTC-safe.
- Keep docker-compose local run and VM smoke path stable.

## Out of Scope

- Performance tuning/index optimization (EPIC-024).
- New external channels beyond Telegram.
- Marketing/bulk broadcast notifications unrelated to booking reminder contract.

## Dependencies

- EPIC-007 (observability and reliability baseline)
- EPIC-010 (idempotency and delivery retry baseline)
- EPIC-021 (business timezone policy)
- EPIC-022 (informative notification context baseline)

## Planned PR Groups

- `group-01.md`: reminder domain policy + storage/ADR baseline
- `group-02.md`: reminder scheduler/dispatcher integration with Telegram delivery path
- `group-03.md`: regression hardening + delivery docs synchronization

## ADR

- Accepted: `docs/90-decisions/adr-0020-booking-reminder-scheduling-and-delivery-policy.md`

## Delivery Note

- 2026-02-10: PR groups `group-01`, `group-02`, `group-03` implemented; reminder scheduling/dispatch, observability, tests, and delivery docs synchronized.

## Epic Acceptance Target

- System schedules and sends reminder to client 2 hours before appointment start in `BUSINESS_TIMEZONE`.
- If booking is created less than 2 hours before slot start, reminder is not scheduled/sent.
- Reminder processing is idempotent and resilient to retries/restarts (no duplicate reminders for one booking).
- Local/VM smoke and regression checks remain green with new reminder behavior.
