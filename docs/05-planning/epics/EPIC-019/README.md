# EPIC-019 — Auto-registration on bot start + bootstrap-only initial user baseline

Status: DONE
Started: 2026-02-09
Roadmap source: `docs/05-planning/epics.md`

## Goal

Ensure that any Telegram user who opens the bot can enter the product without `Пользователь не найден`, while keeping first-deploy database baseline limited to bootstrap owner identity only.

## Scope

- Add idempotent auto-registration on `/start` for unknown Telegram users with baseline `Client` role.
- Persist Telegram nickname (`users.telegram_username`) during start-time registration and keep deterministic normalization for `@nickname` flows.
- Refactor bootstrap/seed behavior so fresh deploy contains only bootstrap owner user (`BOOTSTRAP_MASTER_TELEGRAM_ID`) plus required RBAC roles.
- Remove start-path behavior that can return `Пользователь не найден` to first-time users.
- Update local and VM smoke documentation to validate new registration and baseline-data contract.

## Out of Scope

- Master display-name rename flow (planned in `EPIC-020`).
- New Telegram transport mode (webhook/polling policy is unchanged).
- Multi-tenant or multi-branch identity partitioning.

## Dependencies

- EPIC-013 (bootstrap identity and owner rights)
- EPIC-017 (role-first `/start`)
- EPIC-018 (nickname-based master assignment)

## Planned PR Groups

- `group-01.md`: baseline bootstrap/seed contract refactor
- `group-02.md`: start-time auto-registration and no-not-found entry behavior
- `group-03.md`: regression coverage and delivery doc synchronization

## ADR

- Proposed: `docs/90-decisions/adr-0016-auto-registration-and-bootstrap-only-seed-policy.md`

## Epic Acceptance Target

- New Telegram user gets deterministic, idempotent registration on `/start` without pre-provisioning.
- `users.telegram_username` is captured in registration flow and available for admin nickname workflows.
- Fresh DB contains no extra users beyond bootstrap owner before first organic user start.
- Local/VM smoke paths explicitly verify bootstrap-only baseline and first-user auto-registration.

## Merge-Gate Check At Close

- Local `docker compose up -d --build` path and smoke checks are passing with updated baseline assertions (`users=1`, `masters=1` on clean seed).
- Regression and full local tests are passing:
  - `.venv/bin/pytest -q` -> `83 passed`
  - smoke-aligned suite from `docs/04-delivery/local-dev.md` -> `54 passed`
- Docs are synchronized for changed delivery behavior:
  - `docs/04-delivery/local-dev.md`
  - `docs/04-delivery/deploy-vm.md`
- ADR decision is finalized:
  - `docs/90-decisions/adr-0016-auto-registration-and-bootstrap-only-seed-policy.md` (`Status: Accepted`)

## Close-Out Validation

- Task matrix complete: `T-001`..`T-006` marked `DONE` in `tasks.md`.
- PR groups complete: `group-01`, `group-02`, and `group-03` marked `DONE`.
- Intentional deviation at close step:
  - CI status (Bandit, pip-audit, Gitleaks, reviewer gate) is not executed in this local close workflow; enforce in PR pipeline before merge.
