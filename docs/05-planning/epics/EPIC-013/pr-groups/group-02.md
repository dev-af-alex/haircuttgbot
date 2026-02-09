# EPIC-013 / PR Group 02

## Objective

Implement bootstrap-master-only Telegram button flows for adding/removing masters and add observable/auditable outcomes for those actions.

## Scope

- Add button-first master administration branch in master menu.
- Restrict add/remove actions to bootstrap master only.
- Implement idempotent add/remove master data operations with soft deactivation on remove.
- Emit structured audit events and dedicated metrics labels for master-admin outcomes.
- Add automated tests for bootstrap success and non-bootstrap denial paths.

## Included tasks

- T-003 - DONE
- T-004 - DONE

## Mergeability and runtime safety

- Existing booking/schedule callback flows remain backward-compatible.
- No destructive schema change; remove flow uses `masters.is_active = false`.
- `docker compose up -d` and existing smoke command path stay valid.

## Acceptance checks

1. Bootstrap master can add a user as master and remove another active master via callbacks.
2. Non-bootstrap master receives deterministic `ru` deny response on admin callbacks.
3. Add/remove operations are idempotent and preserve referential integrity.
4. Audit logs include actor, target, action, and outcome for master-admin attempts.
5. Metrics expose `bot_api_master_admin_outcomes_total{action,outcome}`.

## Validation commands

```bash
.venv/bin/pytest -q tests/test_telegram_master_callbacks.py tests/test_observability.py
.venv/bin/pytest -q
docker compose up -d --build
docker compose ps -a
```

## Group status

Status: DONE
Completed at: 2026-02-09

## Risks and mitigations

- Risk: bootstrap-only guard bypass via stale callback payload.
  - Mitigation: enforce runtime bootstrap check before callback state transition.
- Risk: removing masters may break historical data references.
  - Mitigation: use soft deactivation (`is_active=false`) instead of delete.
