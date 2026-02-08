# EPIC-004 — Client booking flow

Status: IN_PROGRESS

## Goal

Deliver the client journey for selecting a master/service, viewing available slots, and creating one active future booking with confirmation.

## Scope

- Client-facing command flow for master + service selection.
- Availability calculation that excludes occupied slots, day-off blocks, and lunch break windows.
- Booking creation with DB validations and one-active-future-booking policy.
- Russian-language booking flow messages and confirmation notification.
- Smoke-test/docs updates for local booking scenario.

## Out of scope

- Cancellation flows for client/master (EPIC-005).
- Master schedule editing commands (EPIC-006).
- Observability and VM deployment hardening (EPIC-007/008).

## Acceptance criteria

- Client can select a master and one service option: haircut, beard, haircut+beard.
- Availability returns only valid slots inside working hours and excludes occupied/day-off/lunch intervals.
- Client cannot hold more than one active future booking.
- Successful booking sends confirmation to relevant participants.
- Local smoke path can validate booking creation end-to-end.

## Dependencies

- EPIC-002 schema + migrations + seeds.
- EPIC-003 auth + RBAC baseline.

## Deliverables

- Booking availability/creation application services and API/handler integration.
- Tests for booking constraints and one-active-booking rule.
- Updated product/architecture/delivery docs for booking flow.

## Planned PR groups

- Group 01: service catalog + availability query baseline.
- Group 02: booking creation + one-active-booking enforcement.
- Group 03: flow polish, tests expansion, smoke/doc-sync, acceptance verification.
