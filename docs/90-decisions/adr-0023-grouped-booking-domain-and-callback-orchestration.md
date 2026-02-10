# ADR-0023: Grouped booking domain and callback orchestration

Date: 2026-02-10
Status: Accepted
Deciders: Backend maintainers

## Context

Client now needs to place one grouped request for multiple people. Each participant requires explicit name identity, can be scheduled independently (including different masters/days), and must support participant-level cancellation. Existing organizer-level `FR-017` policy remains unchanged and must not be silently weakened.

## Decision

- Grouped booking is represented directly in `bookings` with participant-level records using:
  - `organizer_user_id` (owner client who manages grouped participants),
  - `booking_group_key` (group request correlation key),
  - `manual_client_name` as required participant identity field.
- Participant records are created with `client_user_id = NULL`; organizer ownership is tracked through `organizer_user_id`.
- Organizer regular booking policy (`FR-017`) stays unchanged for standard single-client bookings (`client_user_id` path).
- Client callback flow adds grouped orchestration actions:
  - `cg` start grouped flow,
  - text input for participant name,
  - `cga` add next participant,
  - `cgf` finish grouped flow.
- Participant-level cancellation reuses existing cancellation path with ownership expanded to `(client_user_id OR organizer_user_id)`.
- Master notifications use participant name context from `manual_client_name` for grouped records.

## Alternatives considered

- Reuse plain independent single bookings with no grouping metadata.  
  Rejected: cannot provide coherent grouped flow, participant-aware cancellation UX, or traceable grouped operation semantics.
- Relax `FR-017` and treat grouped booking as unlimited organizer bookings.  
  Rejected: explicitly disallowed by product decision.
- Force same master/day for all participants in one request.  
  Rejected: explicitly disallowed by product decision.

## Consequences

- Requires schema/API/callback contract updates with backward-compatible migration strategy.
- Increases state orchestration complexity and regression surface in Telegram callback flows.
- Needs explicit smoke and test coverage for grouped create + participant cancel and unchanged organizer ownership constraints.
