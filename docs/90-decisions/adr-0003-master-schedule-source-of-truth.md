# ADR-0003: Master schedule source of truth and conflict precedence

Date: 2026-02-08
Status: Proposed
Deciders: Backend maintainers

## Context

EPIC-006 introduces master-managed schedule edits (day-off, lunch updates, manual bookings). We need one authoritative model for how these updates are persisted and how conflict checks are evaluated by availability and booking flows.

## Decision

TBD in EPIC-006 implementation.

## Alternatives considered

- Keep lunch/day-off/manual records in separate paths with independent conflict logic.
- Normalize all schedule restrictions as availability blocks and keep booking conflicts independent.
- Introduce a materialized daily schedule snapshot table for read path speed.

## Consequences

- Clarifies ownership and conflict semantics before implementing schedule write paths.
- Reduces risk of diverging rules between availability and booking validation.
- Requires follow-up update to set Status=Accepted and fill final decision details.
