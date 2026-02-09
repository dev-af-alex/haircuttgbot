# EPIC-013 / PR Group 03

## Objective

Synchronize local/VM smoke runbooks with bootstrap-master administration behavior and harden regression/merge-gate checks for EPIC-013 closure.

## Scope

- Update `docs/04-delivery/local-dev.md` smoke path with bootstrap add/remove and non-bootstrap deny checks.
- Update `docs/04-delivery/deploy-vm.md` post-deploy/rollback checklists with bootstrap and master-admin validation coverage.
- Add focused regression tests for master-admin edge cases (idempotent add, bootstrap self-remove denial, soft deactivation behavior).
- Mark EPIC tasks and group status for merge readiness.

## Included tasks

- T-005 - DONE
- T-006 - DONE

## Mergeability and runtime safety

- No destructive DB operations are introduced.
- Existing booking/schedule smoke checks stay intact and are extended, not replaced.
- Docker-compose local run path remains unchanged.

## Acceptance checks

1. Local runbook includes bootstrap config + master add/remove smoke steps.
2. VM runbook includes bootstrap provisioning checks and rollback-safe verification updates.
3. Regression tests cover master-admin edge scenarios and pass in CI path.
4. Existing booking/schedule smoke and test suite stay green.

## Validation commands

```bash
.venv/bin/pytest -q tests/test_master_admin.py tests/test_telegram_master_callbacks.py
.venv/bin/pytest -q
docker compose up -d --build
docker compose ps -a
```

## Group status

Status: DONE
Completed at: 2026-02-09

## Risks and mitigations

- Risk: smoke script drift between local and VM runbooks.
  - Mitigation: both docs point to the same canonical local smoke path and explicit bootstrap checks.
- Risk: master-admin regressions in future refactors.
  - Mitigation: dedicated regression tests (`tests/test_master_admin.py`) added to default pytest path.
