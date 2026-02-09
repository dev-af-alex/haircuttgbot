# EPIC-017 — Role-first entry UX and master identity texts

Status: DONE
Owner: TBD
Last updated: 2026-02-09

## Goal

Simplify Telegram start/booking UX by removing the intermediate main menu and using human-readable master identity in client-facing booking flows.

## Scope

- Route role-resolved users directly to role panel (`Client` or `Master`) on `/start`.
- Replace command-list style `/start` text with barbershop greeting message.
- Show master display name (not `Master ID`) in client master-selection and booking-confirmation messages.
- Keep RBAC, idempotency, and current compose runtime behavior stable.

## Out of scope

- Nickname-based master assignment flow (`@...`) from EPIC-018.
- New booking business rules beyond current FR/NFR baseline.
- Web/mobile interfaces outside Telegram bot UX.

## Constraints and references

- Product FR: `docs/01-product/requirements.md` (`FR-001`, `FR-002`, `FR-003`, `FR-005`, `FR-008`, `FR-021`)
- Security/RBAC baseline: `docs/02-nfr/security.md`
- Performance and idempotency constraints: `docs/02-nfr/performance.md`
- Reliability/observability baseline: `docs/02-nfr/reliability.md`
- Privacy baseline: `docs/02-nfr/privacy.md`
- Local runtime + smoke: `docs/04-delivery/local-dev.md`
- VM deployment verification: `docs/04-delivery/deploy-vm.md`
- ADR stub: `docs/90-decisions/adr-0014-master-display-identity-policy.md`

## Acceptance criteria

- `Главное меню` section is removed from user-visible navigation; role-resolved users land directly in `Client` or `Master` panel on bot start.
- `/start` sends barbershop greeting text instead of command-list style response.
- Client master-selection and booking-confirmation texts show master display name (not `Master ID`) consistently.
- Regression and smoke coverage validate direct role landing, greeting message contract, and master-name rendering in selection/confirmation flows.

## Dependencies

- EPIC-012 interactive button UX baseline
- EPIC-013 bootstrap identity and master administration baseline
- EPIC-015 readable localized time and mobile UX baseline

## Risks and controls

- Risk: start-flow refactor causes role misrouting or unknown-role regressions.
  - Control: shared route helper and direct tests for client/master/unknown-role entry cases.
- Risk: master name rendering is inconsistent when profile fields are partially missing.
  - Control: one centralized display-name policy with deterministic fallback order from ADR.
- Risk: menu removal breaks existing callback/message contracts.
  - Control: callback regression tests for unchanged action handlers after direct landing.

## Delivery summary

- Group-01: decision and entry-routing foundation.
- Group-02: client-facing master identity text rollout.
- Group-03: regression/smoke/doc sync and epic closure prep.

## Merge-gate check at close

- `docker compose up -d` and canonical smoke checks pass after each group merge.
- Epic docs (`README`, `tasks`, `pr-groups`) are status-aligned and synchronized.
- ADR decision for master display identity policy is accepted and linked.
- CI security gates (Bandit, pip-audit, Gitleaks) remain passing on PRs.

## Close-out validation

- Task matrix complete: `T-001`..`T-008` marked `DONE` in `tasks.md`.
- PR groups complete: `group-01`, `group-02`, and `group-03` marked `DONE`.
- Local verification completed during implementation:
  - `.venv/bin/pytest -q` -> `78 passed`.
  - smoke-aligned suite from `docs/04-delivery/local-dev.md` -> `45 passed`.
- Intentional deviation at close step:
  - CI status (including Bandit, pip-audit, Gitleaks) is not executed in this local close workflow; enforce in PR pipeline before merge.
