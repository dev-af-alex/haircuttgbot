# EPIC-009 / PR Group 01

Status: TODO

## Objective

Ship the first mergeable abuse-protection baseline: finalize throttling decision and implement minimal runtime guardrails without breaking local compose behavior.

## Included tasks

- T-001 — Define abuse-control strategy and event contract
- T-002 — Implement throttling middleware for Telegram-facing commands

## Why this grouping

- Establishes a clear decision and executable baseline before broader NFR/doc finalization.
- Keeps first PR technically meaningful and small enough for merge-commit workflow.
- Delivers immediate protective value without coupling to final closure activities.

## Acceptance checks

- ADR exists for abuse-control strategy with explicit alternatives and consequences.
- Runtime throttling policy is enforced for Telegram-facing command paths.
- Structured logs/metrics capture allow and deny outcomes.
- `docker compose up -d --build` remains passing and smoke path stays runnable.

## Merge readiness gates

- Local compose run remains healthy and smoke test is executable.
- No secrets/PII introduced into repository artifacts.
- Documentation is synchronized for behavior/interface changes.

## Task status

- T-001: TODO
- T-002: TODO
