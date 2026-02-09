# ADR-0011: Variable-duration availability and overlap strategy

Date: 2026-02-09
Status: Accepted
Deciders: Backend maintainers, product owner

## Context

EPIC-014 introduces per-service durations (initially 30 and 60 minutes). The system previously assumed fixed 60-minute slots. We needed one deterministic strategy for availability generation and conflict checks across bookings, lunch breaks, day-off intervals, and manual bookings while preserving idempotent Telegram retries.

## Decision

- Canonical interval model: half-open intervals (`[start, end)`).
- Service duration source: `services.duration_minutes` (with safe fallback to baseline defaults in runtime/tests).
- Availability strategy:
  - service-aware requests build slots using requested service duration;
  - start-time step uses 30-minute increments for service-aware generation;
  - service-unaware legacy paths remain on current 60-minute baseline until UX wiring is completed.
- Overlap enforcement: one shared overlap predicate (`start < other_end AND other_start < end`) used by booking create, manual booking, day-off conflict checks, and availability block filtering.

## Alternatives considered

1. Keep fixed hourly grid and only vary booking end time.
   - Rejected: hides valid 30-minute inventory and produces inconsistent slot behavior.
2. Fully free-form minute-level starts.
   - Rejected: too much callback/state complexity for MVP.
3. 30-minute grid with half-open interval checks.
   - Chosen: balances UX simplicity and conflict correctness for baseline 30/60 services.

## Consequences

Positive:

- Consistent overlap handling across all relevant write paths.
- Enables variable-duration inventory without breaking existing compose runtime.

Negative:

- Transitional period where some legacy flows still request slots without passing `service_type` and therefore remain on 60-minute generation.

Follow-up actions:

- Group-03 will wire selected service type through interactive callback flow end-to-end.
- Expand smoke docs for explicit 30-minute and 60-minute end-to-end checks.
