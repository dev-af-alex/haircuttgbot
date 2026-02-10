# ADR-0020: Booking reminder scheduling and delivery policy

Date: 2026-02-10
Status: Accepted
Deciders: Backend maintainers, product owner

## Context

The product requires reminder notifications exactly 2 hours before appointment start, but only for bookings created earlier than that boundary.
Reminder processing must remain safe under retries/restarts and reuse existing Telegram delivery/idempotency behavior.
Timezone semantics must align with `BUSINESS_TIMEZONE` while persistence stays UTC-safe.

## Decision

- Introduce durable reminder state linked to booking with explicit due timestamp and delivery status.
- Schedule reminder only when `booking_created_at <= slot_start - 2h` in business-time semantics.
- Execute reminder dispatch through a background poller path with idempotent send/update transaction boundary.
- Reuse Telegram delivery observability/retry policy and prevent duplicate reminders for one booking.

## Alternatives considered

1. Send reminders inline during booking creation.
   - Pros: simpler implementation path.
   - Cons: cannot guarantee exact due-time delivery or restart safety.
2. Use in-memory scheduler only.
   - Pros: minimal DB/schema changes.
   - Cons: reminders are lost on restart and hard to make deterministic.
3. Send reminders for all future bookings regardless of create time.
   - Pros: simpler eligibility logic.
   - Cons: violates explicit product rule for bookings created less than 2 hours before slot.

## Consequences

Positive:

- Reminder behavior is deterministic and restart-safe.
- Eligibility rule is explicit and testable at timezone boundaries.
- Delivery reliability reuses existing idempotency/observability baseline.

Negative:

- Adds schema and runtime worker complexity.
- Requires additional regression matrix for time-boundary and replay scenarios.

Follow-up actions:

- Add boundary tests for `<2h`, `=2h`, and `>2h` booking lead times.
- Add smoke and operational runbook checks for reminder processing outcomes.
