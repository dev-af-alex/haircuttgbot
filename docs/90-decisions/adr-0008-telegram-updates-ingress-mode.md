# ADR-0008: Telegram updates ingress mode for aiogram runtime

Date: 2026-02-09
Status: Accepted
Deciders: Product/Engineering (haircuttgbot)

## Context

Current runtime exposes internal Telegram-like HTTP contracts but does not process real Telegram updates from chat interactions. EPIC-011 requires wiring aiogram handlers to existing business services and selecting an operational ingress mode compatible with local docker-compose and single-VM deployment.

The decision must balance:

- local developer ergonomics and reproducibility;
- VM operational security (TLS/public ingress expectations);
- reliability constraints and retry behavior from EPIC-010.

## Decision

Adopt a polling-first runtime for EPIC-011 baseline.

- aiogram updates ingress mode is configured by `TELEGRAM_UPDATES_MODE`.
- Supported values in baseline:
  - `polling` (default): start aiogram long polling when `TELEGRAM_BOT_TOKEN` is configured.
  - `disabled`: do not start Telegram updates runtime.
- Unsupported/unknown mode values are treated as `disabled` for safe startup behavior.
- Webhook mode is deferred to later EPIC-011 PR groups when handler and ingress path are fully implemented.

## Alternatives considered

- Webhook-first runtime
  - Not chosen for Group 01 because it requires public TLS ingress and webhook lifecycle orchestration before handler baseline exists.
- Dual-mode (`polling` local + `webhook` VM) in initial slice
  - Not chosen for Group 01 to avoid partial/inconsistent webhook behavior and keep first PR mergeable.

## Consequences

- Positive:
  - Real Telegram updates path is available immediately in local and VM runtime without public webhook endpoint.
  - Startup remains safe when token is absent or mode is disabled.
  - Compose reproducibility is preserved with deterministic default (`polling`).
- Negative:
  - VM currently relies on outbound-only Telegram connectivity; inbound webhook operational model is not available yet.
  - Webhook-specific retry/ingress controls remain deferred.
- Follow-ups:
  - Implement role-specific aiogram handlers wired to existing booking/schedule services (EPIC-011 Group 02).
  - Revisit webhook mode once handler baseline and ingress requirements are ready (EPIC-011 Group 03+).
