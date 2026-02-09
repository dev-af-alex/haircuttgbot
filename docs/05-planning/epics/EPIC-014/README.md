# EPIC-014 — Service duration model and variable-slot booking engine

Status: DONE  
Owner: TBD  
Last updated: 2026-02-09

## Goal

Replace fixed 60-minute booking assumptions with per-service duration support (starting with 30 and 60 minutes) while preserving RBAC, idempotency, and existing Telegram interactive flows.

## Scope

- Add service-duration configuration to service catalog with MVP defaults.
- Update availability generation to support variable durations and reject partial overlaps with lunch/day-off/manual bookings.
- Update booking/cancel pipelines and idempotency checks so duplicate Telegram deliveries remain safe with variable durations.
- Keep `docker compose` local run and smoke path working across incremental PR groups.

## Out of scope

- Dynamic master-specific pricing.
- Arbitrary custom duration editing from Telegram UI.
- Time zone expansion beyond current project baseline.

## Acceptance criteria

- Service catalog persists configurable duration per service and exposes baseline defaults.
- Availability and conflict checks prevent overlaps for 30-minute and 60-minute services across bookings, lunch, day-off, and manual bookings.
- Booking/cancel flows remain retry-safe and idempotent under duplicate delivery conditions.
- Smoke coverage includes at least one end-to-end 30-minute and one 60-minute scenario.

## Dependencies

- EPIC-004 client booking flow
- EPIC-006 master schedule management
- EPIC-010 Telegram delivery idempotency hardening
- EPIC-012 interactive button UX

## Risks and controls

- Risk: overlap edge cases at boundary times regress booking correctness.
  - Control: explicit overlap matrix tests at repository/service layers.
- Risk: callback flow state becomes stale as duration choices change.
  - Control: deterministic stale-callback responses and callback payload versioning checks.
- Risk: incremental rollout breaks local smoke.
  - Control: each PR group includes compose smoke + targeted Telegram callback tests.

## Delivery summary

- Group-01: service catalog schema + seed defaults + duration validation baseline.
- Group-02: duration-aware availability and shared overlap predicate across write paths.
- Group-03: interactive callback wiring for service-aware slots, idempotency regression coverage, and smoke/doc sync for mixed-duration checks.
