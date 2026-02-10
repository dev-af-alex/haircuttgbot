# EPIC-022 — PR Group 01

Status: DONE

## Goal

Define and implement notification identity/manual-client data contracts so later Telegram changes can be merged safely without breaking local runtime.

## Included Tasks

- T-001
- T-002
- T-003

## Planned Changes

- Finalize ADR for identity context precedence and privacy-safe handling.
- Add/adjust persistence contract for manual client free-text and optional notification contact snapshot.
- Implement deterministic context resolver used by notification builders.
- Preserve existing compose startup and seed flow behavior.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_seed.py tests/test_booking.py tests/test_telegram_master_callbacks.py`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `docker compose ps -a`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable independently and should land before message-template and callback flow changes.
- Keeps docker-compose path runnable while introducing backward-compatible data model/service primitives.
