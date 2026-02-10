# ADR-0018: Configurable business timezone and UTC persistence boundaries

Date: 2026-02-10
Status: Accepted
Deciders: Backend maintainers, product owner

## Context

Current booking and schedule behavior is time-dependent (same-day lead-time guardrail, date-slot generation, readable time output), but timezone ownership is not explicit and may depend on host/runtime defaults.
The product requires running bot logic in a configured business timezone (for example, Moscow/Saint Petersburg) while keeping deterministic behavior across local and VM environments.

## Decision

- Introduce runtime config `BUSINESS_TIMEZONE` with strict IANA validation and a safe default (`Europe/Moscow`).
- Keep DB timestamps persisted in UTC and perform timezone conversion only at domain/presentation boundaries.
- Evaluate same-day and business-date rules in configured business timezone, not host OS timezone.
- Keep existing booking/schedule invariants unchanged from product perspective.

## Alternatives considered

1. Fix timezone permanently to `Europe/Moscow` without configuration.
   - Pros: minimal implementation complexity.
   - Cons: cannot reuse deployment in other business timezones.
2. Store and process all timestamps in local timezone only.
   - Pros: simpler UI formatting.
   - Cons: higher risk of inconsistent comparisons and DST-related bugs.
3. Keep current implicit host-timezone behavior.
   - Pros: zero code changes now.
   - Cons: nondeterministic behavior across environments and unclear operational contract.

## Consequences

Positive:

- Deterministic temporal behavior across environments.
- Portable deployment with explicit timezone policy.
- Cleaner boundaries between persistence and business-time rules.

Negative:

- Requires broad regression coverage for timezone-sensitive paths.
- Adds configuration and migration pressure for delivery docs/runbooks.

Follow-up actions:

- Keep timezone regression tests for non-UTC and DST-sensitive zones.
- Keep local/VM runbooks synchronized with timezone configuration and smoke verification.
