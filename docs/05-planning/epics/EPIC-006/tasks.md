# EPIC-006 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Define master schedule command and ownership contracts — Status: DONE
  - Scope: define request/response contracts for master schedule commands and ownership resolution for target master profile.
  - Acceptance:
    - contracts cover day-off, lunch-break update, and manual-booking command payloads.
    - ownership validation path is documented and reused across schedule handlers.
  - Estimation: 1 dev-day
  - Dependencies: none

- T-002 — Implement day-off write path for master — Status: DONE
  - Scope: add use case for creating/updating master day-off intervals as availability blocks.
  - Acceptance:
    - master can create day-off interval for own profile.
    - invalid/overlapping day-off requests are rejected with deterministic message.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Recompute availability against day-off updates — Status: DONE
  - Scope: ensure client availability endpoints reflect day-off changes immediately.
  - Acceptance:
    - day-off intervals are excluded from available slots after update.
    - regression tests cover boundary overlap semantics.
  - Estimation: 1 dev-day
  - Dependencies: T-002

- T-004 — Implement lunch break update flow — Status: TODO
  - Scope: add master use case for changing lunch break window with validation against work hours.
  - Acceptance:
    - lunch update persists for target master.
    - invalid lunch interval (outside work window / wrong duration rules) is rejected.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-005 — Apply lunch update to booking/availability validation — Status: TODO
  - Scope: wire updated lunch window into availability and booking conflict checks.
  - Acceptance:
    - booking and availability reject slots overlapping updated lunch window.
    - tests cover new lunch boundaries and prior default behavior.
  - Estimation: 2 dev-days
  - Dependencies: T-004

- T-006 — Add master manual booking flow — Status: TODO
  - Scope: implement Telegram/manual-booking path for master-offline requests with ownership and overlap guards.
  - Acceptance:
    - master can create manual booking for own schedule.
    - overlapping/manual booking conflicts are rejected.
  - Estimation: 3 dev-days
  - Dependencies: T-003, T-005

- T-007 — Expand smoke and finalize doc sync for EPIC-006 — Status: TODO
  - Scope: extend local smoke and synchronize API/planning/delivery docs for master schedule management behavior.
  - Acceptance:
    - smoke includes day-off/lunch-update impact checks and manual-booking scenario.
    - doc-sync checklist items are updated with no unresolved epic-level drift.
  - Estimation: 1 dev-day
  - Dependencies: T-006
