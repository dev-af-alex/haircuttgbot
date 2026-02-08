# EPIC-007 / PR Group 01

Status: TODO

## Objective

Ship the first mergeable observability slice: structured logging baseline plus Prometheus metrics endpoint/instrumentation.

## Included tasks

- T-001 — Define observability event schema and redaction policy
- T-002 — Implement structured JSON logging baseline
- T-003 — Expose metrics endpoint and latency/outcome instrumentation

## Why this grouping

- Delivers immediate operational visibility without coupling to backup/recovery workflow.
- Establishes telemetry contracts reused by later alert definitions and runbook checks.
- Keeps runtime change bounded to application layer and mergeable in one PR.

## Acceptance checks

- Startup, booking, schedule, and RBAC-deny logs are structured JSON and follow schema.
- No secrets/bot token values are present in emitted logs.
- `/metrics` is reachable and includes request latency + booking outcome counters.
- `docker compose up -d --build` + current smoke test path remain passing.

## Merge readiness gates

- CI remains green (`pytest`, Bandit, pip-audit, Gitleaks, migration checks).
- Tests verify logging redaction and metrics updates on booking flow calls.
- Docs updated for new operational endpoints/fields where behavior changed.
- Merge method remains merge-commit.

## Task status

- T-001: TODO
- T-002: TODO
- T-003: TODO
