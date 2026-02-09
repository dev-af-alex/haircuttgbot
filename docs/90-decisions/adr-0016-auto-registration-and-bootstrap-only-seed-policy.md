# ADR-0016: Auto-registration and bootstrap-only initial-user baseline policy

Date: 2026-02-09
Status: Accepted
Deciders: Backend maintainers, product owner

## Context

Current behavior still relies on pre-provisioned users in several flows, which creates a failure mode where first-time Telegram user entry can return `Пользователь не найден`.
For first production deployment, product scope requires a clean initial state with no extra users except bootstrap owner configured by `BOOTSTRAP_MASTER_TELEGRAM_ID`.
The system also depends on Telegram nickname identity for bootstrap owner master administration workflows.

## Decision

- Register unknown Telegram users idempotently on `/start` with baseline `Client` role.
- Persist Telegram nickname in `users.telegram_username` during registration/start path using deterministic normalization rules.
- Seed/startup baseline on clean DB creates only required roles and bootstrap owner user/master; no extra demo users are pre-created.
- Replace `/start` not-found outcome with registration + role landing behavior, while preserving deterministic RBAC deny responses for restricted actions.

## Alternatives considered

1. Keep strict pre-provisioned-user contract and return `Пользователь не найден` for unknown users.
   - Rejected: does not satisfy first-entry UX requirement and increases manual operational overhead.
2. Keep demo/pre-seeded user set on clean deploy for convenience.
   - Rejected: conflicts with explicit bootstrap-only initial data requirement.
3. Register users lazily on first privileged command instead of `/start`.
   - Rejected: still leaves entry path inconsistent and complicates role-first UX contracts.

## Consequences

Positive:

- First-time user onboarding becomes deterministic without manual DB preparation.
- Deployment baseline becomes cleaner and closer to production reality.
- Nickname-dependent admin flows rely on consistently captured identity data.

Negative / trade-offs:

- Requires refactor of existing seed/bootstrap assumptions and related smoke checks.
- Requires regression coverage updates for start-entry and role mapping behavior.

Follow-ups:

- Implement tasks in `docs/05-planning/epics/EPIC-019/tasks.md`.
- Update local/VM delivery docs and smoke commands after implementation.
