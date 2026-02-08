# EPIC-005 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Add cancellation domain contract baseline — Status: DONE
  - Scope: define canonical cancellation status/reason contract and shared validation primitives used by API/Telegram handlers.
  - Acceptance:
    - cancellation reason field and status transitions are codified in one shared contract.
    - contract docs clarify when reason is required vs optional.
  - Estimation: 1 dev-day
  - Dependencies: none

- T-002 — Implement client self-cancel use case — Status: DONE
  - Scope: add client cancellation path that allows canceling only the caller's active future booking.
  - Acceptance:
    - client can cancel own active future booking.
    - attempts to cancel a non-owned booking or past/inactive booking are rejected.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Wire client cancellation notification — Status: DONE
  - Scope: send cancellation confirmation notifications for client-initiated cancellation to relevant participants.
  - Acceptance:
    - client receives cancellation confirmation.
    - master-facing cancellation notice is emitted for affected booking.
  - Estimation: 1 dev-day
  - Dependencies: T-002

- T-004 — Implement master cancel flow with mandatory reason — Status: DONE
  - Scope: add master cancellation path requiring non-empty textual reason and enforcing master ownership of booking.
  - Acceptance:
    - master cancellation without reason is rejected.
    - master can cancel only bookings tied to their own master profile.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-005 — Deliver reasoned cancellation notifications — Status: DONE
  - Scope: ensure master cancellation reason is propagated to client notification payload and localized ru message templates.
  - Acceptance:
    - client notification for master-initiated cancellation includes provided reason.
    - tests validate notification payload/message content for both role-initiated paths.
  - Estimation: 2 dev-days
  - Dependencies: T-003, T-004

- T-006 — Expand smoke and finalize doc sync for EPIC-005 — Status: DONE
  - Scope: extend local smoke steps and synchronize planning/product/delivery docs for cancellation behavior.
  - Acceptance:
    - smoke test covers at least one successful client cancellation and one rejected master-without-reason cancellation.
    - doc-sync checklist items are updated with no unresolved epic-level drift.
  - Estimation: 1 dev-day
  - Dependencies: T-005
