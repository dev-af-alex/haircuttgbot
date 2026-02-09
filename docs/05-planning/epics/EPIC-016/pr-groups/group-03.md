# EPIC-016 — PR Group 03

## Objective

Finalize EPIC-016 with regression hardening and documentation sync for local/VM validation.

## Scope

- Add automated regression coverage for past-slot rejection, occupied-day day-off rejection, and schedule-by-date.
- Update local and VM smoke instructions with explicit EPIC-016 checks.
- Close remaining task/doc-sync items for epic completion readiness.

## Tasks included

- T-007 Expand regression tests for guardrails and calendar constraints - DONE.
- T-008 Update local and VM smoke instructions - DONE.
- T-009 Epic closure and checklist/doc-sync prep - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable independently via merge commit.
- No destructive schema migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0, runtime services healthy).
- Extended smoke path is reproducible from docs without manual hidden steps.

## Acceptance checks

1. Regression suite covers target boundary and conflict scenarios from EPIC-016 acceptance.
2. Local/VM runbooks document the new validation path clearly.
3. Epic artifacts (`README`, `tasks`, `pr-groups`) are status-aligned and ready for close workflow.
4. Canonical smoke and unit tests pass.

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
