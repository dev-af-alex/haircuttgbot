# EPIC-005 — Cancellation and notification flow

Status: IN_PROGRESS

## Goal

Implement cancellation scenarios for client and master roles, including mandatory cancellation reason for master-initiated cancellations and contextual notifications to affected participants.

## Scope

- Client can cancel own active future booking.
- Master can cancel own master-booking assignments with mandatory textual reason.
- Cancellation notifications are sent to impacted client/master with role-aware context.
- RBAC and ownership checks for cancellation actions.
- Local smoke/doc updates for cancellation coverage.

## Out of scope

- Master schedule editing (EPIC-006).
- Observability and VM deployment hardening (EPIC-007/008).

## Acceptance criteria

- Client can cancel only their own active future booking.
- Master cancellation requires non-empty reason and is rejected otherwise.
- Master can cancel bookings only for their own schedule.
- Cancellation notifications include required context; client receives master reason when cancellation is master-initiated.
- `docker compose up -d --build` path remains healthy and local smoke covers cancellation success/reject scenarios.

## Dependencies

- EPIC-004 booking flow baseline.

## Deliverables

- Cancellation use cases for client and master roles with transactional status update.
- Notification payload updates for cancellation events.
- Tests for authorization, reason validation, and notification contract.
- Updated delivery/docs artifacts for cancellation flow.

## Planned PR groups

- Group 01: client cancellation baseline (own booking only) + confirmation notification.
- Group 02: master cancellation with mandatory reason + ownership guardrails.
- Group 03: smoke/doc sync and acceptance hardening.
