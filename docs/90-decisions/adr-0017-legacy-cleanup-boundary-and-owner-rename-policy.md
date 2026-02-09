# ADR-0017: Legacy cleanup boundary and owner-only master rename policy

Date: 2026-02-09
Status: Accepted
Deciders: Backend maintainers, product owner

## Context

The project has not been deployed to production yet, so backward-compatibility branches aimed at historical rollout states increase complexity without current operational value.
At the same time, product requirements now include bootstrap-owner-only capability to rename masters.
The system must keep deterministic RBAC, observability, and local/VM delivery runbooks while introducing this new admin action.

## Decision

- Remove pre-deploy compatibility branches for slot-selection flows and keep one active baseline where service-aware slot selection always requires `service_type`.
- Keep a single 30-minute step for availability generation while preserving service-specific duration checks.
- Introduce bootstrap-owner-only master rename flow in Telegram admin menu (`Управление мастерами` -> `Переименовать мастера`).
- Emit explicit outcome reasons for rename actions (`success`, `rejected`, `denied`) through audit events and `bot_api_master_admin_outcomes_total`.

## Alternatives considered

1. Keep all compatibility branches until after first production release.
   - Pros: lower short-term code churn.
   - Cons: preserves unnecessary complexity and increases maintenance/testing burden before deploy.
2. Remove compatibility branches but postpone rename to a later epic.
   - Pros: narrower initial refactor scope.
   - Cons: delays requested owner-admin capability and causes avoidable repeated touch points in admin flow.
3. Implement rename for all masters, not just bootstrap owner.
   - Pros: less role-specialized UX.
   - Cons: violates current authorization policy and expands security risk surface.

## Consequences

Positive:

- Cleaner codebase and smaller behavioral surface before first deploy.
- Deterministic, policy-aligned owner admin capabilities.
- More focused regression matrix around supported baseline only.

Negative:

- Cleanup may require broad refactor across services/tests/docs.
- Rename flow adds callback/state complexity that must be tightly tested.

Follow-up actions:

- Keep regression coverage for baseline cleanup invariants and owner-only rename contracts.
- Keep local/VM smoke docs synchronized with rename validation path.
