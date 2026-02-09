# EPIC-011 / PR Group 03

Status: DONE

## Objective

Harden local validation for real Telegram runtime and close test/documentation gaps before epic closure.

## Included tasks

- T-005 — Add tests and real Telegram validation runbook updates

## Why this grouping

- Completes the operator-facing validation path for real Telegram in polling mode.
- Closes the last test/documentation task before epic close-out.
- Keeps scope mergeable without changing core business logic.

## Acceptance checks

- Automated tests cover command mapping and key rejection paths.
- `docs/04-delivery/local-dev.md` includes reproducible real Telegram validation steps.
- `docker compose up -d --build` and existing smoke script remain passing.

## Merge readiness gates

- Local compose runtime and smoke remain healthy.
- Security gates remain wired and passing locally where environment allows.
- Docs are synchronized for runtime/validation behavior.

## Task status

- T-005: DONE

