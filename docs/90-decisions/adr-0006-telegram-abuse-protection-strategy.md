# ADR-0006: Telegram abuse-protection strategy baseline

Date: 2026-02-09
Status: Proposed
Deciders: Engineering

## Context

MVP still has open NFR TODOs for abuse prevention and rate limiting. EPIC-009 introduces an initial protection baseline for Telegram-facing command paths while preserving single-VM operational simplicity.

## Decision

TODO in EPIC-009 Group 01.
Candidate direction: enforce per-telegram-user throttling windows using Redis-backed counters, return deterministic rejection responses, and emit structured deny events/metrics for operations.

## Alternatives considered

- In-memory per-process throttling without shared state.
- Reverse-proxy-only request limiting without application-level context.
- No throttling in MVP and rely only on reactive manual blocking.

## Consequences

Positive, negative, and follow-up actions will be finalized after Group 01 implementation and smoke validation.
