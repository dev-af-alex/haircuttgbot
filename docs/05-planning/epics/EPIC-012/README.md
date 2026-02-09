# EPIC-012 — Telegram interactive button UX

Status: IN_PROGRESS
Owner: TBD

## Goal

Replace slash-command driven primary journeys with interactive Telegram buttons (inline/reply keyboard + callbacks) for both `Client` and `Master` flows while preserving RBAC, idempotency, and existing booking/schedule behavior.

## Scope

In scope:
- Button-first navigation for client booking and cancellation flows.
- Button-first navigation for master schedule management and booking cancellation with reason.
- Callback routing and state handling with deterministic stale-action responses in `ru` locale.
- Local and VM verification updates for interactive scenarios.

Out of scope:
- New business capabilities beyond existing FR set.
- Non-Telegram interfaces (web/mobile).
- Replacing current HTTP internal contracts used by smoke tests.

## Constraints and references

- Product FR: `docs/01-product/requirements.md` (`FR-003`..`FR-021`)
- Security/RBAC and throttling: `docs/02-nfr/security.md`
- Performance/idempotency constraints: `docs/02-nfr/performance.md`
- Reliability/observability baseline: `docs/02-nfr/reliability.md`
- Privacy/minimization: `docs/02-nfr/privacy.md`
- Runtime and checks: `docs/04-delivery/local-dev.md`, `docs/04-delivery/deploy-vm.md`
- Decision stub: `docs/90-decisions/adr-0009-telegram-interactive-menu-state-strategy.md`
- Group-01 callback contract: `docs/05-planning/epics/EPIC-012/callback-contract.md`

## Epic acceptance

- `Client` can complete booking and cancel booking using interactive buttons without mandatory `/` commands.
- `Master` can manage schedule (view, day-off, lunch update, manual booking) and cancel booking with reason using interactive buttons without mandatory `/` commands.
- Callback handling is RBAC-safe and idempotent; stale/duplicate actions return deterministic `ru` messages.
- Local and VM runbooks include at least one interactive smoke scenario per role while preserving existing `docker compose up -d` path.
