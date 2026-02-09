# EPIC-020 — PR Group 01

Status: DONE

## Goal

Define and execute the legacy cleanup boundary so runtime and code paths are reduced to one pre-deploy baseline without breaking local compose behavior.

## Included Tasks

- T-001
- T-002
- T-003

## Planned Changes

- Finalize ADR for what compatibility scaffolding is removed vs retained.
- Remove dead/compatibility branches tied to undeployed historical states.
- Refactor service and handler wiring to baseline-only paths.
- Keep seed/startup and role/admin flows deterministic after cleanup.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_seed.py tests/test_telegram_callbacks.py tests/test_telegram_client_callbacks.py tests/test_telegram_master_callbacks.py`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `docker compose ps -a`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable independently and should land before rename feature work.
- Keeps docker-compose path runnable while reducing internal branching complexity.
