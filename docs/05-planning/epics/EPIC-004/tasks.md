# EPIC-004 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Add booking service options contract — Status: DONE
  - Scope: define canonical service options (`haircut`, `beard`, `haircut_beard`) and ru labels used in booking flow.
  - Acceptance:
    - service option enum/constants are centralized and reused by booking handlers.
    - docs/API contract reflect service option identifiers.
  - Estimation: 1 dev-day
  - Dependencies: none

- T-002 — Implement availability slot generation service — Status: DONE
  - Scope: generate 60-minute slots in 10:00-21:00 work window for selected master/date.
  - Acceptance:
    - slots align to policy window and default duration.
    - availability response excludes past times for current day.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Exclude blocked times from availability — Status: DONE
  - Scope: remove occupied bookings, day-off blocks, and lunch break intervals from generated slots.
  - Acceptance:
    - conflicting slots are not returned.
    - tests cover overlap edges (slot start/end touching blocked interval boundaries).
  - Estimation: 2 dev-days
  - Dependencies: T-002

- T-004 — Add client booking creation use case — Status: DONE
  - Scope: create booking for selected master/service/slot with transactional DB write and validation.
  - Acceptance:
    - booking persists with correct status and service option.
    - occupied slot cannot be booked concurrently.
  - Estimation: 2 dev-days
  - Dependencies: T-003

- T-005 — Enforce one active future booking per client — Status: DONE
  - Scope: block create flow when client already has active future booking.
  - Acceptance:
    - second future booking attempt is rejected with ru message.
    - tests verify boundary around current/past bookings.
  - Estimation: 1 dev-day
  - Dependencies: T-004

- T-006 — Wire Telegram booking flow and confirmations — Status: TODO
  - Scope: connect handlers/menu callbacks for select master → select service → pick slot → confirm booking.
  - Acceptance:
    - client completes booking flow through Telegram interactions.
    - confirmation notification is sent to client (and master if implemented in current notifier path).
  - Estimation: 3 dev-days
  - Dependencies: T-004, T-005

- T-007 — Extend smoke test + finalize doc sync for EPIC-004 — Status: TODO
  - Scope: update local smoke and architecture/product docs for booking flow behavior.
  - Acceptance:
    - local smoke includes one successful booking scenario and one rejection scenario.
    - doc-sync checklist items are resolved or explicitly marked N/A.
  - Estimation: 1 dev-day
  - Dependencies: T-006
