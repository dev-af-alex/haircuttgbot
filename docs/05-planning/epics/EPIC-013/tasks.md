# EPIC-013 tasks

Legend:
- Size: S (<=1 dev-day), M (1-2 dev-days), L (2-3 dev-days)
- Status: TODO / IN_PROGRESS / DONE / BLOCKED

## Task list

- T-001 (M) - Finalize bootstrap provisioning design and env contract - Status: DONE
  - Output: agreed startup/bootstrap strategy (migration vs seed responsibility), env variable contract for bootstrap Telegram ID, and explicit failure modes.
  - Acceptance checks:
    - ADR records decision, alternatives, and consequences.
    - `.env.example` and runtime docs define bootstrap config key(s) and validation rules.
  - Dependencies: none
  - PR group: group-01

- T-002 (M) - Implement idempotent baseline role + bootstrap master provisioning - Status: DONE
  - Output: startup-safe provisioning flow that ensures `Client`/`Master` roles and bootstrap master user/profile exist or are updated.
  - Acceptance checks:
    - Repeated bootstrap runs are idempotent and do not duplicate records.
    - Startup fails with clear error when bootstrap Telegram ID is missing/invalid.
    - Automated tests cover happy path and fail-fast path.
  - Dependencies: T-001
  - PR group: group-01

- T-003 (L) - Implement bootstrap-only master add/remove Telegram flows - Status: DONE
  - Output: button-first management commands for adding/removing masters, with safeguards for self-removal and unknown users.
  - Acceptance checks:
    - Non-bootstrap users are denied with deterministic `ru` response and audit event.
    - Add/remove operations are idempotent and preserve referential integrity.
    - Tests cover RBAC, validation, and edge cases.
  - Dependencies: T-002
  - PR group: group-02

- T-004 (S) - Extend observability and security events for master-admin actions - Status: DONE
  - Output: structured audit events and metrics labels for master add/remove attempts and outcomes.
  - Acceptance checks:
    - Audit logs include actor telegram ID, target telegram ID, action, and outcome.
    - No secret leakage in logs for validation failures.
  - Dependencies: T-003
  - PR group: group-02

- T-005 (M) - Update local/VM smoke checks and delivery docs - Status: TODO
  - Output: synchronized runbooks and smoke scripts validating bootstrap presence and master admin scenarios.
  - Acceptance checks:
    - `docs/04-delivery/local-dev.md` includes bootstrap config + add/remove validation steps.
    - `docs/04-delivery/deploy-vm.md` includes operator checks for bootstrap provisioning and rollback triggers.
  - Dependencies: T-002, T-003
  - PR group: group-03

- T-006 (S) - Regression and merge-gate hardening for epic closure - Status: TODO
  - Output: focused regression tests and CI/readiness checklist for epic completion.
  - Acceptance checks:
    - Existing booking/schedule smoke paths remain green after master-admin changes.
    - Epic closure checklist links implemented PR groups and updated SSOT docs.
  - Dependencies: T-004, T-005
  - PR group: group-03

## PR groups overview

- group-01: architecture decision + bootstrap provisioning foundation (mergeable without changing existing operator flows).
- group-02: bootstrap-master Telegram administration flows + security/audit coverage.
- group-03: smoke/doc synchronization + regression hardening + closure readiness.
