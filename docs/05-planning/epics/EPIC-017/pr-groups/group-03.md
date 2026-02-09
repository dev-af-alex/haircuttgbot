# EPIC-017 — PR Group 03

## Objective

Finalize EPIC-017 with regression hardening and delivery-doc synchronization for role-first entry and master-name text contracts.

## Scope

- Add automated regression tests for direct role landing and greeting behavior.
- Add automated regression tests for master-name rendering in selection/confirmation texts.
- Update local and VM smoke instructions for EPIC-017 checks.
- Prepare epic closure artifacts and checklist alignment.

## Tasks included

- T-006 Expand regression tests for role-first entry and name rendering - DONE.
- T-007 Synchronize local and VM smoke validation docs - DONE.
- T-008 Epic closure and checklist/doc-sync prep - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable independently via merge commit.
- No destructive schema migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0, runtime services healthy).
- Extended smoke path remains reproducible from docs.

## Acceptance checks

1. Regression suite covers role-direct `/start` landing for client/master and unknown-role handling.
2. Regression suite verifies master-name rendering in client selection and confirmation outputs.
3. Local/VM runbooks include EPIC-017 text and flow validation steps.
4. Epic docs are status-aligned and ready for close workflow.

## Validation commands

```bash
docker compose up -d --build
docker compose ps -a
.venv/bin/pytest -q
curl -fsS http://127.0.0.1:8080/health
```

## Group status

Status: DONE
Completed at: 2026-02-09
