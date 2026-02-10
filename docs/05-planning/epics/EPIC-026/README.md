# EPIC-026 — Grouped booking for multiple people by one client

Status: DONE
Started: 2026-02-10
Roadmap source: `docs/05-planning/epics.md`

## Goal

Allow one client to place a grouped booking request for multiple participants, each identified by organizer-provided name, with independent slot/master/date assignment and participant-level cancellation.

## Scope

- Add grouped booking flow for client with participant list management.
- Require participant name input for each grouped participant.
- Allow each participant booking to target any available master/date/slot independently.
- Preserve organizer-level `FR-017` policy (no relaxation of one-active-future-booking ownership constraint).
- Add participant-level cancellation flow and participant-aware notifications.

## Out of Scope

- Payment splitting or group-level billing.
- Batch cancellation that cancels all participants at once.
- New non-Telegram user interfaces.

## Dependencies

- EPIC-004 (client booking flow baseline)
- EPIC-005 (cancellation and notification baseline)
- EPIC-012 (interactive callback UX baseline)
- EPIC-014 (service duration semantics)
- EPIC-021 (business timezone consistency)
- EPIC-025 (2-month paginated date navigation)

## Planned PR Groups

- `group-01.md`: grouped booking domain model + callback contract + ADR baseline
- `group-02.md`: grouped participant create flow integration (multi-master/multi-day) with guardrail preservation
- `group-03.md`: participant-level cancellation, regressions, and smoke/doc synchronization

## ADR

- Accepted: `docs/90-decisions/adr-0023-grouped-booking-domain-and-callback-orchestration.md`

## Epic Acceptance Target

- Client can add at least two participants with explicit names inside one grouped booking request.
- Each participant can be assigned independently to different masters/dates/slots in the same request.
- Participant-level cancellation is available and does not require full-group cancellation.
- Organizer-level `FR-017` behavior remains unchanged and deterministic.
- Local/VM smoke and regression coverage include grouped create + participant cancel scenarios.

## Delivered

- Added grouped participant booking model fields in bookings (`organizer_user_id`, `booking_group_key`) with backward-compatible ownership behavior for existing flows.
- Implemented client grouped callback flow with explicit participant-name input and independent participant assignment across masters/dates.
- Implemented participant-level cancellation through organizer ownership path and participant-aware cancellation labels/texts.
- Updated regression tests and delivery runbooks for grouped create/cancel scenarios.

## Merge Gates

- Local merge gates: satisfied (`.venv/bin/pytest -q`, docker compose up/seed/health/metrics/down smoke path).
- Intentional deviation: CI green status and PR-time SAST/dependency/secrets scans were not re-run in this epic-close step.
