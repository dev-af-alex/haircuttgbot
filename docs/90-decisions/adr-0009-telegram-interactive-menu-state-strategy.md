# ADR-0009: Telegram interactive menu state strategy

Date: 2026-02-09
Status: Proposed
Deciders: Backend maintainers

## Context

EPIC-012 replaces slash-command primary flows with interactive buttons for `Client` and `Master`. We need a consistent strategy for:
- callback payload format and size bounds,
- short-lived user interaction state (selected master/service/slot/menu step),
- stale-button behavior after state transitions or timeouts,
- idempotent processing under duplicate Telegram deliveries,
- RBAC-safe routing and auditable denials.

Without an explicit decision, handlers may diverge and cause inconsistent UX, duplicate write operations, or fragile menu restoration.

## Decision

TBD in EPIC-012 group-01.

Candidate direction: use compact, versioned callback actions with server-side short-lived interaction state keyed by Telegram user ID and role scope; enforce deterministic stale-action responses and idempotent write-path bridging to existing booking/schedule services.

## Alternatives considered

1. Fully stateless callbacks carrying all context in payload.
2. Hybrid stateless payload + selective server-side session cache.
3. Full finite-state-machine session persisted in database.
4. Keep slash commands as primary path and limit buttons to shortcuts.

## Consequences

Expected positive:
- Unified callback contract across roles and handlers.
- Predictable stale-action UX and easier regression testing.
- Lower risk of duplicate write side effects.

Potential negative:
- Additional complexity in session/state lifecycle management.
- Extra documentation/testing burden for callback compatibility.

Follow-up actions:
- Finalize accepted option in EPIC-012 group-01 and update this ADR status to Accepted.
- Link accepted contract docs and tests from `docs/05-planning/epics/EPIC-012/`.
