# ADR-0015: Master assignment by Telegram nickname resolution policy

Date: 2026-02-09
Status: Proposed
Deciders: TBD

## Context

EPIC-018 changes bootstrap-master add flow from selecting known users to manual nickname input (`@...`). The system must define deterministic behavior for:

- nickname input format validation;
- normalization (case sensitivity and prefix handling);
- resolution when nickname is unknown;
- resolution when multiple candidate records can match historical or incomplete data.

Without one policy, operator feedback and add-master outcomes can be inconsistent and hard to audit.

## Decision

Proposed policy (to finalize in implementation):

- Accept only manual nickname input starting with `@` and matching bounded allowed characters.
- Normalize input before resolution (for example, trim spaces and canonicalize case strategy).
- Resolve against current known Telegram identity mapping source.
- Return deterministic localized outcomes:
  - success (master assigned);
  - invalid format;
  - unknown nickname;
  - ambiguous nickname.
- Keep bootstrap-only RBAC and existing master-admin audit/metric events mandatory for this path.

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

- Finalize validation regex and normalization behavior.
- Add regression tests for all resolution outcomes.
- Synchronize local/VM smoke steps for nickname-first bootstrap flow.
