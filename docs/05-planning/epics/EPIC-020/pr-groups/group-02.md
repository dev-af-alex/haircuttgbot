# EPIC-020 — PR Group 02

Status: DONE

## Goal

Deliver owner-only master rename capability in Telegram admin flow with deterministic authorization, validation, and observability.

## Included Tasks

- T-004
- T-005
- T-006

## Planned Changes

- Add domain operation to rename master profile by target identity.
- Allow only bootstrap owner to execute rename; return explicit deny for non-owner masters.
- Extend master-admin Telegram menus/state to support rename input and confirmation.
- Emit audit/metrics events for `rename` outcomes (`success`, `rejected`, `denied`) with reason codes.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_master_admin.py tests/test_telegram_master_callbacks.py tests/test_observability.py`
- `docker compose up -d --build`
- `curl -fsS http://127.0.0.1:8080/health`
- `curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_master_admin_outcomes_total'`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable after Group 01 cleanup stabilizes the baseline.
- Preserves compose health and existing booking/schedule flows while extending admin capabilities.
