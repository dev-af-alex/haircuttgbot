# ADR-0006: Telegram abuse-protection strategy baseline

Date: 2026-02-09
Status: Accepted
Deciders: Engineering

## Context

MVP still has open NFR TODOs for abuse prevention and rate limiting. EPIC-009 Group 01 introduces the first protection baseline for Telegram-facing command paths while preserving single-VM operational simplicity and avoiding new infra dependencies.

## Decision

Adopt application-level per-user sliding-window throttling for `POST /internal/telegram/*` commands.

- Baseline policy: `8` requests per `10` seconds per `telegram_user_id` (configurable via env).
- User identity keys: `client_telegram_user_id`, `master_telegram_user_id`, `telegram_user_id`.
- Rejections return deterministic `429` payload:
  - `detail`: localized retry guidance
  - `code`: `throttled`
  - `retry_after_seconds`
- Denials emit structured security event `abuse_throttle_deny`.
- Metrics emit `bot_api_abuse_outcomes_total{path,outcome}` with `allow`/`deny`.

## Alternatives considered

- In-memory per-process throttling without shared state.
- Reverse-proxy-only request limiting without application-level context.
- No throttling in MVP and rely only on reactive manual blocking.

## Consequences

### Positive

- Immediate abuse resistance for burst command traffic without external components.
- Deterministic deny contract suitable for bot UX and retry behavior.
- Operational visibility through structured deny events and per-path allow/deny counters.

### Negative

- In-memory counters are process-local and reset on service restart.
- Policy is coarse (same limit for all Telegram command paths).

### Follow-up actions

- EPIC-009 Group 02 may refine limit matrix per command criticality if needed.
- Future scale-out can migrate counters to Redis-backed shared state without changing deny contract.
