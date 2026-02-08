# EPIC-001 / PR Group 01

Status: DONE

## Objective

Deliver the first mergeable baseline where local compose runs real services with health checks and minimal `bot-api` skeleton.

## Included tasks

- T-001 — Replace placeholder compose with runtime baseline
- T-002 — Add minimal bot-api service scaffold
- T-003 — Define local smoke test and sync local-dev docs

## Why this grouping

- Produces immediate runnable baseline required by all next PR groups.
- Keeps change set focused on runtime bootstrap and local verification.
- Safe to merge independently without waiting for CI security implementation.

## Acceptance checks

- `docker compose up -d` starts `bot-api`, `postgres`, `redis` successfully.
- Health checks report healthy services.
- Smoke test in `docs/04-delivery/local-dev.md` is complete and passes.
- `docker compose down` returns environment to clean state.

## Merge readiness gates

- DoD checklist sections for local run and docs are satisfied.
- No secrets committed; env values are externalized.
- Existing repository checks continue passing.
- No unit tests added in this group; runtime bootstrap is validated via compose health checks and smoke test (automated tests planned in T-005).

## Task status

- T-001: DONE
- T-002: DONE
- T-003: DONE
