# EPIC-015 — Localized readable time and final mobile UX polish

Status: DONE
Owner: TBD
Last updated: 2026-02-09

## Goal

Deliver readable, localized (`ru`) booking/schedule time output and phone-friendly Telegram button layouts across `Client` and `Master` interactive flows.

## Scope

- Replace raw timestamp output in user-visible booking/schedule notifications with human-readable localized strings.
- Apply consistent readable time formatting for create/cancel/update paths used by both roles.
- Normalize interactive keyboard row widths so primary actions remain usable on mobile screens.
- Preserve existing RBAC, idempotency, and compose-based local run behavior.

## Out of scope

- New business capabilities outside current booking/schedule/admin features.
- New non-Telegram interfaces (web/mobile app UI).
- Per-user locale switching beyond current `ru` MVP baseline.

## Constraints and references

- Product FR: `docs/01-product/requirements.md` (`FR-003`..`FR-021`)
- Security/RBAC and abuse controls: `docs/02-nfr/security.md`
- Performance/idempotency constraints: `docs/02-nfr/performance.md`
- Reliability/observability baseline: `docs/02-nfr/reliability.md`
- Privacy/minimization baseline: `docs/02-nfr/privacy.md`
- Local runtime and smoke path: `docs/04-delivery/local-dev.md`
- VM deploy verification path: `docs/04-delivery/deploy-vm.md`
- Decision stub: `docs/90-decisions/adr-0012-readable-time-and-mobile-keyboard-contract.md`

## Acceptance criteria

- Client-facing and master-facing booking/schedule messages render readable localized (`ru`) time/date output instead of raw timestamps.
- Interactive keyboard layouts for key journeys stay within phone-friendly row widths across main menus and booking/schedule steps.
- Automated regression coverage verifies formatting consistency for create/cancel/update notifications.
- Local and VM smoke paths include explicit checks for readable-time output and mobile-usable button menus.

## Dependencies

- EPIC-012 interactive button UX baseline
- EPIC-013 bootstrap/master administration flows
- EPIC-014 variable-slot duration support

## Risks and controls

- Risk: readable formatting changes create inconsistent strings across handlers.
  - Control: single shared formatter utility + centralized message template update + regression tests.
- Risk: button row changes regress callback flows or remove critical actions from reachable menus.
  - Control: keyboard layout helper constraints + callback integration tests for client/master/admin menus.
- Risk: mobile UX polish work accidentally changes business logic.
  - Control: keep scope to presentation/menu composition layers and run canonical smoke/tests each PR group.

## Delivery summary

- Group-01: finalize formatting/layout contract (ADR) and implement shared formatter/layout foundation.
- Group-02: apply readable time + mobile layout updates across client interactive flows.
- Group-03: apply master/admin flows, expand regression coverage, and sync local/VM smoke docs for epic closeout.

## Merge-gate check at close

- Local `docker compose up -d` and smoke/test validation passed during group implementations and close-out checks.
- Documentation sync completed for local and VM runbooks (`docs/04-delivery/local-dev.md`, `docs/04-delivery/deploy-vm.md`).
- ADR requirement satisfied by accepted `docs/90-decisions/adr-0012-readable-time-and-mobile-keyboard-contract.md`.
- Intentional deviation at close step: CI/SAST/dependency/secrets gate status cannot be verified from this local close operation; enforce in PR/merge pipeline.
