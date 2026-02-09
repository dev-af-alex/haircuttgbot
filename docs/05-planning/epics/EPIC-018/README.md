# EPIC-018 — Manual master assignment by Telegram nickname (`@...`)

Status: DONE
Owner: TBD
Last updated: 2026-02-09

## Goal

Replace bootstrap-master add flow based on selecting existing users with manual `@nickname` input, while preserving RBAC, auditability, and deterministic localized operator feedback.

## Scope

- Add add-master flow in `Управление мастерами` that accepts only manual `@nickname` input.
- Implement deterministic nickname resolution and operator feedback for unknown/ambiguous input.
- Persist nickname-based assignment outcome in current role/master model with audit event continuity.
- Keep remove-master flow and existing bootstrap-only RBAC constraints intact.

## Out of scope

- New identity providers beyond Telegram nickname and existing Telegram user-id mapping.
- Changes to booking/schedule business rules.
- Multi-branch or non-Telegram administration interfaces.

## Constraints and references

- Product FR: `docs/01-product/requirements.md` (`FR-001`, `FR-002`, `FR-008`, `FR-021`)
- Security/RBAC and audit baseline: `docs/02-nfr/security.md`
- Performance and idempotency constraints: `docs/02-nfr/performance.md`
- Reliability/observability baseline: `docs/02-nfr/reliability.md`
- Privacy baseline: `docs/02-nfr/privacy.md`
- Local runtime + smoke: `docs/04-delivery/local-dev.md`
- VM deployment verification: `docs/04-delivery/deploy-vm.md`
- ADR stub: `docs/90-decisions/adr-0015-master-assignment-by-nickname-resolution-policy.md`

## Acceptance criteria

- In `Управление мастерами` add-master flow accepts only manual nickname input starting with `@` and rejects invalid formats.
- System resolves/stores nickname-based assignment with deterministic behavior when nickname is unknown or ambiguous, with localized operator feedback.
- Existing add/remove master RBAC and auditability guarantees stay intact.
- Regression and smoke coverage include success and validation-failure scenarios for nickname-based assignment.

## Dependencies

- EPIC-013 bootstrap identity and master administration baseline
- EPIC-017 role-first entry and master identity text baseline

## Risks and controls

- Risk: nickname input introduces ambiguous or stale identity mapping.
  - Control: explicit resolution policy and deterministic tie-breaking/reject semantics from ADR.
- Risk: manual text input flow regresses callback/menu state handling.
  - Control: bounded state machine for input-await mode + stale/timeout tests.
- Risk: admin auditability weakens if new path bypasses existing events/metrics.
  - Control: reuse existing master-admin observability events with explicit outcome reasons for nickname path.

## Delivery summary

- Group-01: resolution policy + input-mode foundation.
- Group-02: add-master nickname assignment integration.
- Group-03: regression/smoke/doc sync and close readiness.

## Merge-gate check at close

- `docker compose up -d` and canonical smoke checks pass after each group merge.
- Epic docs (`README`, `tasks`, `pr-groups`) are status-aligned and synchronized.
- ADR decision for nickname resolution policy is accepted and linked.
- CI security gates (Bandit, pip-audit, Gitleaks) remain passing on PRs.

## Close-out validation

- Task matrix complete: `T-001`..`T-009` marked `DONE` in `tasks.md`.
- PR groups complete: `group-01`, `group-02`, and `group-03` marked `DONE`.
- Local verification completed during implementation:
  - `.venv/bin/pytest -q` -> `81 passed`.
  - smoke-aligned suite from `docs/04-delivery/local-dev.md` -> `48 passed`.
  - `docker compose up -d --build`, health/metrics/seed/startup-log smoke commands -> passed.
- Intentional deviation at close step:
  - CI status (including Bandit, pip-audit, Gitleaks) is not executed in this local close workflow; enforce in PR pipeline before merge.
