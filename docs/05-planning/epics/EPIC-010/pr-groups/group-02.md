# EPIC-010 / PR Group 02

Status: DONE

## Objective

Implement delivery retry/error policy observability and complete duplicate-delivery coverage in tests and local smoke.

## Included tasks

- T-003 — Add tests and smoke coverage for duplicate deliveries
- T-004 — Formalize retry/error policy and observability mapping

## Why this grouping

- Keeps idempotency behavior and retry policy implementation in one mergeable increment.
- Adds direct verification in both automated tests and local smoke path.
- Expands observability contract without changing deployment topology.

## Acceptance checks

- Automated tests verify both replayed success and non-cached rejected duplicate-delivery behavior.
- `/metrics` exposes Telegram delivery outcome counters by retry class.
- `docs/04-delivery/local-dev.md` smoke script validates duplicate-delivery replay header contract.
- `docs/03-architecture/apis.md` and `docs/02-nfr/reliability.md` document retry/error classes and observability mapping.

## Merge readiness gates

- Existing docker-compose run path remains unchanged and reproducible.
- CI quality/security gates remain green.
- No secrets/PII introduced.

## Task status

- T-003: DONE
- T-004: DONE
