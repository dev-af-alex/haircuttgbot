# EPIC-020 Tasks

Status legend: TODO / IN_PROGRESS / DONE / BLOCKED.

- T-001 — Finalize ADR for legacy-cleanup boundary and owner-only master-rename policy (`adr-0017`).  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-002 — Remove pre-deploy backward-compatibility code paths and simplify runtime to one active baseline.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-003 — Refactor affected services/handlers/tests to align with cleaned baseline contract without behavioral regressions.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-004 — Implement owner-only master rename domain operation with deterministic validation and RBAC deny reasons.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-005 — Add Telegram master-admin rename interaction flow (menu, input/state, confirmations) for bootstrap owner.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-006 — Wire observability for rename outcomes (success/rejected/denied) and audit event payload consistency.  
  Est: 1 dev-day.  
  PR group: 02.  
  Status: DONE.

- T-007 — Add regression coverage for legacy-cleanup invariants and baseline flow continuity.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-008 — Add regression coverage for master rename success, non-owner deny, and invalid input paths.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-009 — Sync `local-dev` and `deploy-vm` smoke contracts with rename flow and legacy-cleaned baseline checks.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.
