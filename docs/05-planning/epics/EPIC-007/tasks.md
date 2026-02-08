# EPIC-007 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Define observability event schema and redaction policy — Status: TODO
  - Scope: define structured log event names/fields for booking lifecycle and security denials; codify forbidden fields (token/secrets/raw PII payloads).
  - Acceptance:
    - required fields for startup, booking create/cancel, schedule update, and `rbac_deny` are documented.
    - policy explicitly states what cannot be logged.
  - Estimation: 1 dev-day
  - Dependencies: none

- T-002 — Implement structured JSON logging baseline — Status: TODO
  - Scope: add/revise app logging so core lifecycle events follow schema and redaction rules.
  - Acceptance:
    - startup and core booking/schedule/security actions emit structured JSON logs.
    - regression test verifies secret/token values are not present in logs.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Expose metrics endpoint and latency/outcome instrumentation — Status: TODO
  - Scope: add `/metrics` endpoint and instrument API request latency plus booking success/failure counters.
  - Acceptance:
    - `/metrics` responds in Prometheus format.
    - counters/latency series update after booking flow requests.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-004 — Implement PostgreSQL backup workflow + runbook — Status: TODO
  - Scope: define and document repeatable backup command set for single VM (logical dump + retention guidance).
  - Acceptance:
    - runbook includes prerequisites, backup command, retention, and storage location guidance.
    - local execution commands are reproducible from docs.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-005 — Validate restore rehearsal and data-integrity checks — Status: TODO
  - Scope: document/execute restore rehearsal against local stack and verify booking/schedule data recovery semantics.
  - Acceptance:
    - rehearsal includes restore into clean DB state and integrity verification queries.
    - local-dev smoke/runbook docs reference the rehearsal path.
  - Estimation: 2 dev-days
  - Dependencies: T-004

- T-006 — Add minimal alert baseline and finalize doc sync — Status: TODO
  - Scope: define alert thresholds/triggers for service-down and booking error spike; sync checklists/docs.
  - Acceptance:
    - alert rules and response notes are documented.
    - doc-sync checklist items for observability/reliability changes are resolved.
  - Estimation: 1 dev-day
  - Dependencies: T-002, T-003, T-005
