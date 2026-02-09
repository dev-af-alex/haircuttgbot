# ADR-0009: Telegram interactive menu state strategy

Date: 2026-02-09
Status: Accepted
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

Adopt a compact versioned callback contract (`hb1|action|context?`) with server-side short-lived menu state:
- callback payload is bounded to 64 bytes and validated before routing;
- action tokens are compact and explicit (`hm`, `cm`, `mm`, `bk`);
- per-user menu state uses TTL (`900s`) for stale-action detection;
- stale/invalid callback interactions return deterministic localized (`ru`) responses;
- callback routes enforce RBAC and emit auditable deny events (`rbac_deny` with `command=callback:<action>`).

Write-side business operations remain delegated to existing idempotent booking/schedule services in later EPIC-012 groups.

## Alternatives considered

1. Fully stateless callbacks carrying all context in payload.
2. Hybrid stateless payload + selective server-side session cache.
3. Full finite-state-machine session persisted in database.
4. Keep slash commands as primary path and limit buttons to shortcuts.

## Consequences

Expected positive:
- Unified callback contract across roles and handlers.
- Predictable stale-action UX and easier regression testing.
- Lower risk of malformed callback handling regressions.

Potential negative:
- Additional in-memory state lifecycle complexity.
- TTL-based menu state can expire during long user pauses and require re-entry via `/start`.

Follow-up actions:
- Extend action map from menu scaffolding to business flows in EPIC-012 group-02/group-03.
- Keep slash-command handlers as fallback until full button-first parity is reached.
