# EPIC-010 / PR Group 01

Status: DONE

## Objective

Establish a mergeable idempotency baseline for Telegram write-side command handling with clear strategy and first implementation slice.

## Included tasks

- T-001 — Define Telegram delivery idempotency strategy and contract
- T-002 — Implement baseline duplicate-delivery guard for write paths

## Why this grouping

- Locks the core decision and delivers immediate protection against duplicate writes.
- Keeps first PR focused and mergeable while preserving current runtime behavior.
- Creates foundation for retry-policy and closure work in later groups.

## Acceptance checks

- ADR exists for delivery/idempotency strategy with alternatives and consequences.
- Duplicate-delivery guard is active for Telegram write-side endpoints.
- Local `docker compose up -d --build` and smoke run remain passing.

## Merge readiness gates

- Compose runtime and existing smoke path remain operational.
- Docs are synchronized for any contract/behavior changes.
- No secrets/PII are introduced in repository artifacts.

## Task status

- T-001: DONE
- T-002: DONE
