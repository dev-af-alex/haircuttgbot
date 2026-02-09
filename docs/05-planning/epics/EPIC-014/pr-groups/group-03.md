# EPIC-014 — PR Group 03

## Objective

Complete end-to-end service-duration behavior in interactive Telegram flows, lock idempotency regressions, and close epic documentation/smoke sync.

## Scope

- T-004 Wire duration selection through interactive client flow.
- T-005 Preserve idempotent booking/cancel behavior with variable durations.
- T-006 Expand automated tests for 30/60 minute scenarios.
- T-007 Update local and VM smoke documentation.
- T-008 Epic closure and doc-sync checks.

## Implemented changes

- Callback flows now pass selected service type into slot generation for both:
  - client interactive booking flow;
  - master manual-booking interactive flow.
- Added regression coverage for:
  - service-driven slot granularity in interactive callbacks;
  - flow-level 30/60 slot behavior;
  - idempotency key separation by `service_type`.
- Synced local and VM smoke docs with explicit mixed-duration checks.
- Completed epic task/status synchronization.

## Acceptance checks

1. Interactive booking flow uses selected service duration when listing slots.
2. Duplicate Telegram deliveries remain replay-safe and service-type sensitive in idempotency keying.
3. Automated tests include mixed-duration scenarios for booking and callback paths.
4. Local compose run + smoke command path from `docs/04-delivery/local-dev.md` passes.

## Tasks included

- T-004 Wire duration selection through interactive client flow - DONE.
- T-005 Preserve idempotent booking/cancel behavior with variable durations - DONE.
- T-006 Expand automated tests for 30/60 minute scenarios - DONE.
- T-007 Update local and VM smoke documentation - DONE.
- T-008 Epic closure and doc-sync checks - DONE.

## Group status

Status: DONE
Completed at: 2026-02-09
