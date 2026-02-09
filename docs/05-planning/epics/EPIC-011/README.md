# EPIC-011 — Real Telegram runtime integration (aiogram updates path)

Status: DONE

## Goal

Connect aiogram update handling to existing booking/schedule services so the system works with real Telegram users, not only internal HTTP contracts.

## Scope

- Implement aiogram runtime updates path in production service (`polling` or `webhook` selected by ADR/config).
- Add command/callback handlers for MVP role journeys using existing service-layer contracts.
- Keep idempotency/throttling/observability behavior aligned with existing Telegram-facing write paths.
- Update local/VM runbooks for reproducible real Telegram validation.

## Out of scope

- Multi-bot support or multi-tenant dispatching.
- Rich conversational redesign beyond existing booking/schedule contract baseline.
- Full async queue migration for Telegram delivery.

## Acceptance criteria

- Real Telegram updates reach running service and trigger business flows for `Client` and `Master`.
- Role enforcement remains effective on handler entry points.
- Duplicate-delivery and abuse-protection baselines remain active for write-side effects.
- Local docker-compose run remains reproducible, with documented real Telegram test scenario.

## Dependencies

- EPIC-003 auth + role enforcement.
- EPIC-004 booking flow.
- EPIC-005 cancellation flow.
- EPIC-006 master schedule management.
- EPIC-010 idempotency/retry policy baseline.

## Deliverables

- Configurable aiogram runtime mode (`polling`/`webhook`) with lifecycle integration.
- Handler layer mapping Telegram updates to existing booking/schedule service operations.
- Tests + docs for real Telegram validation and fallback smoke path.

## Planned PR groups

- Group 01: ingress mode decision + aiogram runtime bootstrap (safe, mergeable).
- Group 02: client/master handler flows wired to existing services with tests.
- Group 03: runbook hardening, end-to-end real Telegram validation notes.
- Group 04: final closure checks and merge-gate sync.

## Notes

- Every PR group must keep `docker compose up -d --build` operational.
- Merge strategy stays merge-commit per repository policy.

## Delivered (Group 01)

- Accepted ingress decision in `docs/90-decisions/adr-0008-telegram-updates-ingress-mode.md`: polling-first runtime with explicit `TELEGRAM_UPDATES_MODE`.
- Implemented aiogram lifecycle bootstrap in FastAPI lifespan with safe startup behavior:
  - starts polling when mode=`polling` and `TELEGRAM_BOT_TOKEN` is configured;
  - emits explicit runtime events and does not crash when token is missing or mode is disabled.
- Added runtime policy unit tests and synchronized local/deploy documentation with new env/runtime behavior.
- Marked `T-001`, `T-002`, and `group-01` as `DONE`.

## Delivered (Group 02)

- Added aiogram command handlers for Telegram chat interaction and wired them into dispatcher bootstrap.
- Implemented client command mapping to booking-flow contracts:
  - `/client_start`, `/client_master`, `/client_slots`, `/client_book`, `/client_cancel`.
- Implemented master command mapping to schedule/cancel contracts:
  - `/master_cancel`, `/master_dayoff`, `/master_lunch`, `/master_manual`.
- Added role-gated command service layer and tests for client/master flow mapping and rejection behavior.
- Marked `T-003`, `T-004`, and `group-02` as `DONE`.

## Delivered (Group 03)

- Added reproducible real Telegram validation runbook section in `docs/04-delivery/local-dev.md` for polling mode.
- Confirmed test coverage includes command mapping and key rejection paths.
- Marked `T-005` and `group-03` as `DONE`.

## Delivered (Group 04)

- Completed final task/doc synchronization for EPIC-011 closure readiness.
- Documented merge-gate readiness and explicit deviation:
  - local compose/smoke/tests/Bandit passed;
  - `pip-audit` could not run in this execution environment due DNS/network restrictions to `pypi.org`.
- Marked `T-006` and `group-04` as `DONE`.

## Epic closure note

- Delivered: real Telegram polling runtime is wired with aiogram handlers for client/master command flows, and local validation runbook now includes reproducible real Telegram checks.
- Merge-gate status: local compose/smoke, tests, and Bandit passed; dependency audit (`pip-audit`) is an intentional environment deviation in this workspace and remains enforced in CI.
