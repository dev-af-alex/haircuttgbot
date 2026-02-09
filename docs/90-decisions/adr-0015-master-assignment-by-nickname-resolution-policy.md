# ADR-0015: Master assignment by Telegram nickname resolution policy

Date: 2026-02-09
Status: Accepted
Deciders: TBD

## Context

EPIC-018 changes bootstrap-master add flow from selecting known users to manual nickname input (`@...`). The system must define deterministic behavior for:

- nickname input format validation;
- normalization (case sensitivity and prefix handling);
- resolution when nickname is unknown;
- resolution when multiple candidate records can match historical or incomplete data.

Without one policy, operator feedback and add-master outcomes can be inconsistent and hard to audit.

## Decision

- Accept only manual nickname input in format `@nickname`.
- Validation rule: body after `@` must match `[A-Za-z0-9_]{5,32}`.
- Normalize input by trimming spaces and lowercasing nickname body before lookup.
- Resolve nickname via `users.telegram_username` (case-insensitive exact match on normalized value).
- Deterministic outcome policy:
  - `invalid_nickname_format`: input does not match required format;
  - `nickname_not_found`: no users match normalized nickname;
  - `nickname_ambiguous`: more than one user matches normalized nickname;
  - success path: exactly one matching user, then existing add-master apply path executes.
- Keep bootstrap-only RBAC and existing master-admin observability events with explicit `reason` codes for nickname outcomes.

## Alternatives considered

- Keep selectable-user add flow and skip manual nickname input.
  - Rejected because it does not satisfy EPIC-018 acceptance.
- Allow nickname input without strict validation.
  - Rejected because it creates inconsistent behavior and support overhead.
- Auto-pick one record on ambiguity.
  - Rejected due to unsafe implicit operator action and audit ambiguity.

## Consequences

Positive:

- Deterministic operator UX and testable add-master outcomes.
- Consistent auditability for sensitive role-assignment actions.

Negative:

- Requires explicit handling for ambiguous legacy identity data.
- May require additional state handling in Telegram callback/message workflow.

Follow-up actions:

- Add regression tests for all resolution outcomes.
- Synchronize local/VM smoke steps for nickname-first bootstrap flow.
