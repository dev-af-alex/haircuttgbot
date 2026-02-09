# EPIC-010 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Define Telegram delivery idempotency strategy and contract — Status: DONE
  - Scope: define duplicate-delivery window, idempotency key shape, and expected response behavior for replayed deliveries.
  - Acceptance:
    - strategy covers write-side Telegram command endpoints.
    - decision and alternatives are captured in ADR.
  - Estimation: 1 dev-day
  - Dependencies: EPIC-003, EPIC-009

- T-002 — Implement baseline duplicate-delivery guard for write paths — Status: DONE
  - Scope: implement idempotency protection for Telegram write-side endpoints.
  - Acceptance:
    - duplicate deliveries do not produce duplicate booking/schedule side effects.
    - deterministic response contract is returned for replayed requests.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Add tests and smoke coverage for duplicate deliveries — Status: DONE
  - Scope: extend unit/integration tests and local smoke to include duplicate delivery scenario.
  - Acceptance:
    - automated tests cover initial delivery and replay behavior.
    - smoke runbook validates at least one idempotency scenario end-to-end.
  - Estimation: 1 dev-day
  - Dependencies: T-002

- T-004 — Formalize retry/error policy and observability mapping — Status: DONE
  - Scope: document and implement retry behavior by failure class with metrics/log events for delivery outcomes.
  - Acceptance:
    - policy defines transient vs terminal failures and retry action.
    - observability docs map metrics/events to retry/duplicate outcomes.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-005 — Final doc-sync and epic closure checks — Status: DONE
  - Scope: complete planning sync and validate merge gates for EPIC-010 closure.
  - Acceptance:
    - epic roadmap/workspace statuses reflect delivered work.
    - PR checklist and delivery docs remain internally consistent.
  - Estimation: 1 dev-day
  - Dependencies: T-003, T-004
