# EPIC-014 — PR Group 02

## Objective

Implement duration-aware slot generation and shared overlap semantics for booking/schedule write paths while keeping compose runtime stable.

## Scope

- T-002 Introduce duration-aware availability slot generator.
- T-003 Enforce interval overlap checks for booking/schedule writes.

## Implemented changes

- Availability now supports optional `service_type` and computes slot length from service catalog duration.
- Duration-aware slot stepping is enabled for service-aware requests (30-minute step for current baseline services).
- Booking create and master manual booking resolve service duration from catalog before computing `slot_end`.
- Day-off, booking, and availability-block overlap checks now share one canonical overlap predicate helper.

## Mergeability and local-run guardrails

- Mergeable independently by merge commit.
- Existing local runtime path remains unchanged:
  - `docker compose up -d --build`
  - `docker compose ps -a`
- Existing smoke suite remains green after duration-aware backend changes.

## Acceptance checks

1. Duration-aware availability behavior is test-covered for 30-minute and 60-minute services.
2. Booking/manual booking writes enforce overlap rejection through shared interval predicate.
3. Canonical smoke test suite from `docs/04-delivery/local-dev.md` passes.
4. No regression in Telegram callback/command baseline tests.

## Tasks included

- T-002 Introduce duration-aware availability slot generator - DONE.
- T-003 Enforce interval overlap checks for booking/schedule writes - DONE.

## Group status

Status: DONE
Completed at: 2026-02-09
