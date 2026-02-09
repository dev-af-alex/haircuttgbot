# EPIC-019 — PR Group 01

Status: DONE

## Goal

Lock and implement clean bootstrap baseline so first deploy has only mandatory roles and bootstrap owner identity, without demo/pre-created extra users.

## Included Tasks

- T-001
- T-002

## Planned Changes

- Finalize ADR for auto-registration + bootstrap-only initial-user policy.
- Refactor seed/bootstrap logic to remove non-essential user bootstrap records.
- Preserve compose startup determinism and idempotent reruns (`docker compose up`, re-seed, restart).

## Acceptance Checks

- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT count(*) FROM users;"`
- `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT count(*) FROM masters;"`
- `.venv/bin/pytest -q tests/test_seed.py`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable independently because it changes baseline data contract first.
- Local compose remains runnable; smoke assertions shift from demo users to bootstrap-only baseline.
