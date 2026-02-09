# EPIC-019 — PR Group 02

Status: DONE

## Goal

Deliver runtime entry behavior where unknown Telegram users are auto-registered on `/start` and never hit `Пользователь не найден`.

## Included Tasks

- T-003
- T-004

## Planned Changes

- Add idempotent registration path in start handler/application service.
- Ensure `Client` role assignment for first-time users without pre-provisioning.
- Persist normalized Telegram nickname during registration and keep nickname usable for admin resolution.
- Replace start-entry not-found branch with deterministic registration + role landing behavior.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_telegram_master_callbacks.py tests/test_master_admin.py`
- `.venv/bin/pytest -q tests/test_idempotency.py`
- `docker compose up -d --build`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable after Group 01 because seed and bootstrap contract are stable.
- Compose runtime remains healthy; only start-entry identity behavior changes.
