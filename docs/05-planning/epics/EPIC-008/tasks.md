# EPIC-008 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Define single-VM deployment contract and release artifact shape — Status: DONE
  - Scope: define VM runtime assumptions, compose/deployment artifact layout, and required environment/secret files.
  - Acceptance:
    - deployment contract includes VM prerequisites, ports, runtime services, and artifact boundaries.
    - secrets/config flow is documented without storing secrets in repo.
  - Estimation: 1 dev-day
  - Dependencies: EPIC-001, EPIC-007

- T-002 — Document deployment runbook with reproducible command path — Status: DONE
  - Scope: complete `docs/04-delivery/deploy-vm.md` with step-by-step deploy procedure from clean VM to running stack.
  - Acceptance:
    - runbook includes provisioning prerequisites, install commands, deploy commands, and verification steps.
    - commands are deterministic and reference canonical smoke checks.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Define rollback procedure and failure triggers — Status: DONE
  - Scope: specify rollback triggers and exact commands for returning to previous known-good deployment.
  - Acceptance:
    - rollback conditions are explicit (failed health/smoke/dependency checks).
    - rollback steps include validation and incident note requirements.
  - Estimation: 1 dev-day
  - Dependencies: T-002

- T-004 — Add deployment verification checklist and handoff notes — Status: TODO
  - Scope: add post-deploy validation checklist aligned with local smoke path and operational handoff.
  - Acceptance:
    - checklist verifies health, metrics, booking flow, and schedule-management flow after deploy.
    - docs link to monitoring/backup/alert runbooks from EPIC-007.
  - Estimation: 1 dev-day
  - Dependencies: T-002

- T-005 — Final doc-sync and epic closure checks — Status: TODO
  - Scope: resolve planning/doc-sync updates and confirm merge gates for deployment baseline.
  - Acceptance:
    - epic roadmap/workspace statuses reflect delivered work.
    - PR checklist and deployment docs are internally consistent.
  - Estimation: 1 dev-day
  - Dependencies: T-003, T-004
