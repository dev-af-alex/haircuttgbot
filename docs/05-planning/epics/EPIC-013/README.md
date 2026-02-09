# EPIC-013 — Bootstrap identity and master administration

Status: IN_PROGRESS
Owner: TBD

## Goal

Guarantee baseline RBAC bootstrap state after migration/startup (required roles + one configured bootstrap master) and provide Telegram-managed add/remove master capabilities restricted to that bootstrap master.

## Scope

In scope:
- Idempotent creation/verification of baseline roles (`Client`, `Master`) in migration/seed startup path.
- Bootstrap master provisioning by configured Telegram user ID from environment.
- Fail-fast startup behavior when bootstrap master config is missing/invalid.
- Telegram button flow for bootstrap master to add/remove other masters with RBAC, auditability, and deterministic localized (`ru`) responses.
- Local and VM smoke updates for bootstrap and master-admin scenarios.

Out of scope:
- Changes to client booking business rules beyond role bootstrap/admin dependencies.
- Bulk import/export of masters.
- Non-Telegram administration UI.

## Constraints and references

- Product FR: `docs/01-product/requirements.md` (`FR-001`, `FR-002`, `FR-008`, `FR-018`, `FR-021`)
- Security and RBAC constraints: `docs/02-nfr/security.md`
- Performance/idempotency constraints: `docs/02-nfr/performance.md`
- Reliability and observability baseline: `docs/02-nfr/reliability.md`
- Privacy/minimization: `docs/02-nfr/privacy.md`
- Runtime checks: `docs/04-delivery/local-dev.md`, `docs/04-delivery/deploy-vm.md`
- Decision stub: `docs/90-decisions/adr-0010-bootstrap-master-provisioning-strategy.md`

## Epic acceptance

- On clean DB bootstrap, required roles and one bootstrap master are present via idempotent startup path.
- Runtime fails fast with explicit operator-facing error when bootstrap config is invalid or missing.
- Only bootstrap master can add/remove masters via Telegram button-first interactions; all attempts are RBAC-checked and audited.
- Local and VM smoke paths include bootstrap-role presence and master add/remove checks while preserving existing docker-compose startup path.
