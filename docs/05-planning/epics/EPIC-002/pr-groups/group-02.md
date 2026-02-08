# EPIC-002 / PR Group 02

Status: DONE

## Objective

Add seed baseline and compose-level migration wiring so local stack is schema-ready by default.

## Included tasks

- T-003 — Add seed data for local smoke scenarios
- T-004 — Wire migrations into local compose lifecycle

## Acceptance checks

- `migrate` one-shot service executes `alembic upgrade head` during `docker compose up -d --build`.
- `python -m app.db.seed` creates at least two master profiles idempotently.
- Smoke flow validates `/health` and seeded masters count.

## Task status

- T-003: DONE
- T-004: DONE
