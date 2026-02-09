# ADR-0007: Telegram delivery idempotency strategy baseline

Date: 2026-02-09
Status: Accepted
Deciders: Engineering

## Context

Telegram webhook/event delivery can replay requests on transient failures. Current baseline lacks a formal idempotency contract for write-side command endpoints, which risks duplicate side effects.

## Decision

Adopt application-level idempotency guards for Telegram write-side endpoints with a bounded replay window.

- Scope:
  - `POST /internal/telegram/client/booking-flow/confirm`
  - `POST /internal/telegram/client/booking-flow/cancel`
  - `POST /internal/telegram/master/booking-flow/cancel`
  - `POST /internal/telegram/master/schedule/day-off`
  - `POST /internal/telegram/master/schedule/lunch`
  - `POST /internal/telegram/master/schedule/manual-booking`
- Key shape: hash of `{path, telegram_user_id, normalized JSON payload}`.
- Replay window: 120 seconds by default (`TELEGRAM_IDEMPOTENCY_WINDOW_SECONDS`).
- Cache policy: store only successful write outcomes (`created/cancelled/applied == true`).
- Replay response: return cached HTTP 200 payload with header `X-Idempotency-Replayed: 1`.

## Alternatives considered

- No idempotency, rely only on DB uniqueness constraints and manual reconciliation.
- Full message queue-based deduplication before API handlers.
- Reverse-proxy hash-based deduplication without application context.

## Consequences

### Positive

- Prevents duplicate write side effects from Telegram delivery retries.
- Keeps response contract deterministic for repeated deliveries in short retry windows.
- Requires no additional infra components for baseline rollout.

### Negative

- In-memory store is process-local and resets on restart.
- Replay window and keying policy can suppress legitimate rapid repeats of identical commands.

### Follow-up actions

- EPIC-010 Group 02 will map retry/error classes to idempotency outcomes and observability signals.
- Future scale-out can move idempotency store to Redis/shared backend while preserving replay contract.
