# EPIC-008 / PR Group 02

Status: DONE

## Objective

Publish a reproducible deploy and rollback command path for a single VM, including explicit failure triggers and post-action validation.

## Included tasks

- T-002 — Document deployment runbook with reproducible command path
- T-003 — Define rollback procedure and failure triggers

## Why this grouping

- Converts Group 01 deployment contract into executable operations.
- Delivers rollback readiness before final epic closure and handoff checklist work.
- Keeps scope documentation-only while validating existing local runtime path remains stable.

## Acceptance checks

- `docs/04-delivery/deploy-vm.md` includes deterministic deploy steps from clean VM to healthy stack.
- Rollback section defines explicit triggers and exact command sequence to restore last known-good release.
- Runbook references canonical smoke checks from `docs/04-delivery/local-dev.md`.

## Merge readiness gates

- `docker compose up -d --build` remains passing locally.
- Smoke test remains executable and passing from `docs/04-delivery/local-dev.md`.
- No secrets are committed; secret handling remains VM-only via `/opt/haircuttgbot/shared/.env`.

## Task status

- T-002: DONE
- T-003: DONE
