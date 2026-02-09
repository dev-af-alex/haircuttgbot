# ADR-0013: Booking-time guardrails and day-off conflict policy

Date: 2026-02-09
Status: Accepted
Deciders: TBD

## Context

EPIC-016 adds three connected behaviors:

- same-day booking must not allow already-passed time windows;
- day-off cannot be set on dates with existing active bookings;
- master schedule view must support explicit date selection.

Current system supports 30-minute and 60-minute services and localized readable time output. Guardrail behavior needs one shared policy to avoid divergent validation between availability rendering and booking confirmation.

## Decision

Accepted contract for EPIC-016 implementation:

- Same-day booking uses minimum lead time `30` minutes from current runtime time.
- Earliest allowed slot start is rounded up to the next `30`-minute boundary used by the slot engine.
- Slot confirmation revalidates the same rule to reject stale callback/selection actions.
- Day-off creation is rejected when target date has at least one active (not canceled) booking for the master.
- Schedule-by-date flow accepts explicit date input from master menu and renders readable localized output for selected date.

## Alternatives considered

1. Exclude only slots strictly earlier than "now" (no lead time).
   - Rejected: allows near-immediate bookings that violate requested UX expectation (`15:00` -> not earlier than `15:30`).
2. Implement only UI-level filtering without server-side revalidation.
   - Rejected: stale callbacks/retries could bypass UI filtering and create inconsistent behavior.
3. Allow day-off over existing bookings and auto-cancel conflicting records.
   - Rejected: high operational risk and undesired automatic cancellation side effects for clients.

## Consequences

- Positive: deterministic and user-readable booking boundaries for same-day flow.
- Positive: protects masters and clients from accidental schedule invalidation.
- Negative: extra validation branches in callback handlers and test matrix expansion.
- Follow-up: keep regression coverage for callback stale-slot confirmation and day-off-on-occupied-date rejection in core smoke/tests.
