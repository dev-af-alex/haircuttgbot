# ADR-0002: Booking slot conflict and interval boundary rules

Date: 2026-02-08
Status: Proposed
Deciders: Delivery team

## Context

EPIC-004 introduces availability generation and booking creation where slot conflict semantics must be consistent across API, DB constraints, and Telegram flow. Ambiguity around interval boundaries (inclusive/exclusive end), timezone handling, and overlap logic can cause double-booking or mismatched availability.

## Decision

TODO during EPIC-004 implementation:

- Decide canonical time model (UTC in DB + local presentation zone vs fully local storage).
- Define interval boundary policy (recommended: `[start, end)` half-open intervals).
- Define overlap rule shared by availability and booking write path.
- Define how lunch/day-off blocks are normalized to slot boundaries.

## Alternatives considered

- Defer interval policy to implementation per handler.
- Rely only on DB uniqueness without shared overlap policy.
- Treat intervals as closed (`[start, end]`) across all checks.

## Consequences

- Positive: consistent conflict behavior and predictable slot results.
- Negative: requires careful migration/test alignment before completion of EPIC-004.
- Follow-up: finalize and mark Accepted in EPIC-004 PR Group 02 or 03.
