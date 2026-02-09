# EPIC-018 — PR Group 01

## Objective

Establish mergeable policy and interaction foundation for nickname-based master assignment before any add-master write-path changes.

## Scope

- Create ADR stub for nickname resolution/ambiguity policy.
- Add bounded callback state for awaiting nickname input from bootstrap master.
- Implement strict nickname format validation and localized rejection messages.
- Keep existing selectable add/remove behavior operational until Group-02.

## Tasks included

- T-001 Finalize nickname-resolution ADR - DONE.
- T-002 Add callback state for manual nickname input - DONE.
- T-003 Implement nickname input validation and localized errors - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable independently via merge commit.
- No destructive schema migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0, runtime services healthy).
- Existing smoke path remains executable after merge.

## Acceptance checks

1. ADR stub defines deterministic handling for valid/invalid/unknown/ambiguous nickname cases.
2. Admin flow can enter nickname-input mode without breaking existing callback menus.
3. Invalid nickname text is rejected with deterministic localized response.
4. Canonical local smoke baseline passes without regressions.

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
