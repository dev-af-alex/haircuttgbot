# EPIC-009 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Define abuse-control strategy and event contract — Status: TODO
  - Scope: define command throttling policy, block/deny behavior, and structured event schema for abuse rejections.
  - Acceptance:
    - policy defines per-user limits, burst windows, and deny response semantics.
    - decision is captured in ADR with alternatives.
  - Estimation: 1 dev-day
  - Dependencies: EPIC-007, EPIC-008

- T-002 — Implement throttling middleware for Telegram-facing commands — Status: TODO
  - Scope: add runtime throttling guard for command paths and emit structured abuse-deny events.
  - Acceptance:
    - repeated burst requests are rejected by configured policy.
    - metrics/logging expose deny outcomes for operational monitoring.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Add tests and smoke checks for abuse-protection scenarios — Status: TODO
  - Scope: add unit/integration coverage and extend smoke procedure with at least one throttle rejection case.
  - Acceptance:
    - test suite covers allow/deny behavior and logging side-effects.
    - local smoke runbook includes abuse-protection validation step.
  - Estimation: 1 dev-day
  - Dependencies: T-002

- T-004 — Finalize secrets/TLS/retention policy docs — Status: TODO
  - Scope: close open TODOs in security/reliability/privacy/performance docs relevant to MVP operations.
  - Acceptance:
    - docs define secrets management lifecycle, TLS ingress policy, retention periods, and SLO targets.
    - delivery docs remain consistent with policy updates.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-005 — Final doc-sync and epic closure checks — Status: TODO
  - Scope: complete planning sync and verify merge gates for EPIC-009 closure.
  - Acceptance:
    - epic roadmap/workspace statuses reflect delivered work.
    - PR checklist and operational docs are internally consistent.
  - Estimation: 1 dev-day
  - Dependencies: T-003, T-004
