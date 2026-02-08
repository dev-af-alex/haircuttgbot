# EPIC-002 / PR Group 03

Status: DONE

## Objective

Add migration regression checks to CI and finish doc-sync for EPIC-002.

## Included tasks

- T-005 — Add schema regression checks in CI
- T-006 — Final doc-sync and epic acceptance verification

## Acceptance checks

- CI runs `alembic upgrade head` against ephemeral Postgres service.
- CI still runs `pytest`, Bandit, pip-audit, and Gitleaks.
- Delivery and architecture docs reflect migration + seeding behavior.

## Task status

- T-005: DONE
- T-006: DONE
