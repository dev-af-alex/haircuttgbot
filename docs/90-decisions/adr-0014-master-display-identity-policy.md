# ADR-0014: Master display identity policy for client-facing texts

Date: 2026-02-09
Status: Accepted
Deciders: TBD

## Context

EPIC-017 requires replacing `Master ID` in client-facing flows with human-readable master identity. Existing data may include different combinations of fields (full name, Telegram username, legacy records), and inconsistent fallback behavior can produce confusing UX and flaky tests.

We need one deterministic policy for how master identity is rendered in:

- client master-selection options;
- booking confirmation/cancel-adjacent client messages;
- future UI text surfaces that expose master identity.

The policy must remain compatible with current schema/runtime and avoid exposing sensitive fields beyond existing product scope.

## Decision

- Introduce one shared formatter for client-facing master identity strings.
- Fallback order:
  - `masters.display_name` (trimmed non-empty value);
  - localized neutral fallback label `Мастер (имя не указано)`.
- Apply the same formatter in:
  - client master-selection options;
  - client booking confirmation preview and created-booking confirmation message;
  - client future-booking cancel list labels.
- Do not expose internal numeric `Master ID` in client-facing texts.

## Alternatives considered

- Continue showing internal `Master ID`.
  - Rejected because it is not human-friendly and contradicts EPIC-017 acceptance.
- Build separate formatting logic per flow.
  - Rejected because it risks drift and inconsistent localization.
- Force mandatory profile name migration before rollout.
  - Deferred because it introduces extra migration risk not required for this epic.

## Consequences

Positive:

- Consistent and readable master identity across client interactions.
- Lower risk of text-contract regressions due to centralized formatter.

Negative:

- Requires explicit fallback semantics for incomplete legacy data.
- May require updates to existing tests and smoke expectations.

Follow-up actions:

- Finalize fallback order and localization keys.
- Add regression coverage for all fallback branches.
- Update local/VM validation steps to assert display-name rendering behavior.
