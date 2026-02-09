# EPIC-011 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Decide Telegram updates ingress mode and runtime contract — Status: DONE
  - Scope: finalize `polling` vs `webhook` strategy for local + single-VM deployment, including security/reliability implications.
  - Acceptance:
    - ADR captures decision, alternatives, and operational consequences.
    - selected mode and required env/config are documented.
  - Estimation: 1 dev-day
  - Dependencies: EPIC-008, EPIC-010

- T-002 — Implement aiogram runtime bootstrap in service lifecycle — Status: DONE
  - Scope: wire aiogram startup/shutdown path in app runtime with safe behavior when token/config is missing.
  - Acceptance:
    - service starts cleanly in docker-compose with and without real token.
    - update-processing runtime path is active per selected mode.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Implement client handler flow mapping to booking contracts — Status: DONE
  - Scope: add Telegram handlers for client booking journey using existing internal services/contracts.
  - Acceptance:
    - client can start flow, select master/service/slot, create and cancel booking from Telegram.
    - role/validation errors return localized user messages.
  - Estimation: 3 dev-days
  - Dependencies: T-002

- T-004 — Implement master handler flow mapping to schedule/cancel contracts — Status: DONE
  - Scope: add Telegram handlers for master cancellation/day-off/lunch/manual-booking actions.
  - Acceptance:
    - master can perform schedule updates and cancellation with mandatory reason.
    - ownership/authorization constraints remain enforced.
  - Estimation: 3 dev-days
  - Dependencies: T-002

- T-005 — Add tests and real Telegram validation runbook updates — Status: DONE
  - Scope: expand automated tests and local delivery docs to include real Telegram validation steps.
  - Acceptance:
    - tests cover handler-to-service mapping and key rejection paths.
    - `docs/04-delivery/local-dev.md` contains reproducible real Telegram check sequence.
  - Estimation: 2 dev-days
  - Dependencies: T-003, T-004

- T-006 — Final doc-sync and epic closure checks — Status: DONE
  - Scope: align epic workspace, roadmap, and delivery/checklist docs for close-out.
  - Acceptance:
    - epic and PR-group statuses reflect delivered scope.
    - merge gates and intentional deviations are documented.
  - Estimation: 1 dev-day
  - Dependencies: T-005
