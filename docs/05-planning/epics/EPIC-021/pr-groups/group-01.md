# EPIC-021 — PR Group 01

Status: DONE

## Goal

Define and implement timezone policy baseline (config + ADR + shared primitives) without changing externally visible booking behavior yet.

## Included Tasks

- T-001
- T-002
- T-003

## Planned Changes

- Accept ADR for business timezone contract and UTC boundary rules.
- Add `BUSINESS_TIMEZONE` config with strict validation and deterministic startup behavior.
- Add shared conversion/date helpers used by later flow refactors.
- Keep compose local run path stable.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_seed.py tests/test_booking.py tests/test_telegram_callbacks.py`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `docker compose ps -a`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable independently and should land before flow-level timezone behavior changes.
- Adds new runtime config contract while preserving current functional baseline.
