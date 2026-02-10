# EPIC-025 — PR Group 01

Status: DONE

## Goal

Define and implement the shared technical contract for 2-month date-window pagination before wiring callback flows.

## Included Tasks

- T-001
- T-002
- T-003

## Planned Changes

- Accept ADR for date horizon and paging behavior.
- Add shared helper(s) for rolling 2-month date window and page boundaries.
- Introduce callback token/state model for safe `next`/`prev` page navigation.
- Preserve current local run behavior and callback safety contracts.

## Acceptance Checks

- `.venv/bin/pytest -q tests/test_timezone.py tests/test_telegram_presentation.py tests/test_telegram_callbacks.py`
- `docker compose up -d --build`
- `docker compose exec -T bot-api python -m app.db.seed`
- `curl -fsS http://127.0.0.1:8080/health`
- `docker compose down`

## Mergeability / Local-run Impact

- Mergeable independently as a non-breaking contract/helper layer.
- Keeps docker-compose local run path stable while preparing paginated UX integration.

## Completion

- T-001: DONE
- T-002: DONE
- T-003: DONE
