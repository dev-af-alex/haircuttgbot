# EPIC-016 — Booking-time guardrails and master calendar constraints

Status: DONE
Owner: TBD
Last updated: 2026-02-09

## Goal

Enforce real-time booking validity and master-calendar consistency: no booking into already-passed same-day windows, no day-off on dates with existing bookings, and date-selectable master schedule view.

## Scope

- Add deterministic same-day booking boundary rules so client availability excludes past windows.
- Enforce day-off write guard that rejects attempts when active bookings already exist on target date.
- Add master-facing date selection for schedule view with readable localized output.
- Keep current RBAC, idempotency, observability, and compose local run behavior stable.

## Out of scope

- Changes to role-entry/start UX (`/start`, panel routing, main-menu removal).
- Master assignment/admin flow changes by `@nickname`.
- New payment/reminder/reporting features.

## Constraints and references

- Product FR: `docs/01-product/requirements.md` (`FR-003`, `FR-005`, `FR-006`, `FR-008`, `FR-010`, `FR-021`)
- Security/RBAC baseline: `docs/02-nfr/security.md`
- Performance and idempotency constraints: `docs/02-nfr/performance.md`
- Reliability/observability baseline: `docs/02-nfr/reliability.md`
- Privacy baseline: `docs/02-nfr/privacy.md`
- Local runtime + smoke: `docs/04-delivery/local-dev.md`
- VM deployment verification: `docs/04-delivery/deploy-vm.md`
- ADR stub: `docs/90-decisions/adr-0013-booking-time-guardrails-and-dayoff-conflict-policy.md`

## Acceptance criteria

- Client cannot confirm booking into already-passed time windows; same-day availability starts from nearest allowed future boundary (example: if now is `15:00`, earliest offered slot is `15:30+`).
- Master cannot set day off for a date with one or more active bookings; bot returns explicit localized rejection.
- Master can choose target date for schedule view (not only current date) and receives readable localized output.
- Automated regression and smoke coverage include: past-slot rejection, day-off rejection on occupied date, and schedule-view-by-date success scenario.

## Dependencies

- EPIC-006 master schedule management baseline
- EPIC-012 interactive button UX baseline
- EPIC-014 variable-duration slot engine
- EPIC-015 readable localized time baseline

## Risks and controls

- Risk: time-boundary logic regresses slot generation near edge times.
  - Control: centralized boundary helper + explicit boundary matrix tests.
- Risk: day-off guard introduces false-positive conflicts due to booking status interpretation.
  - Control: one shared "active booking" predicate reused by day-off validation and tests.
- Risk: date-picker callbacks create stale-state UX regressions.
  - Control: callback contract tests with deterministic stale/invalid-date handling.

## Delivery summary

- Group-01: decision contract + shared guardrail/domain foundation.
- Group-02: callback/API integration for client and master flows.
- Group-03: regression/smoke hardening and doc-sync for close.

## Merge-gate check at close

- Local `docker compose up -d` and canonical smoke checks pass after each group merge.
- Documentation sync complete in local/VM runbooks for new validation steps.
- ADR decision accepted and linked for guardrail/day-off policy.
- CI security gates (Bandit, pip-audit, Gitleaks) are validated in PR pipeline.
