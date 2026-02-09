# EPIC-020 — Pre-deploy legacy cleanup + owner-only master rename flow

Status: DONE
Started: 2026-02-09
Roadmap source: `docs/05-planning/epics.md`

## Goal

Remove backward-compatibility code paths that are unnecessary before first production deployment, and add owner-only capability to rename masters through Telegram flow with deterministic RBAC and auditability.

## Scope

- Remove legacy compatibility branches/adapters that target undeployed historical states.
- Refactor affected flows to one active baseline while preserving existing booking/schedule behavior.
- Add bootstrap-owner-only master rename action in master admin flow.
- Emit deterministic audit/observability outcomes for rename success/reject/deny cases.
- Synchronize local and VM delivery docs with the updated admin and smoke contract.

## Out of Scope

- New role model beyond existing `Client`/`Master` and bootstrap-owner policy.
- Changes to booking duration model, schedule guardrails, or delivery transport mode.
- Non-Telegram administration interfaces.

## Dependencies

- EPIC-018 (nickname-based master assignment baseline)
- EPIC-019 (auto-registration and bootstrap-only seed baseline)

## Planned PR Groups

- `group-01.md`: legacy cleanup boundary + baseline refactor
- `group-02.md`: owner-only master rename domain and Telegram flow
- `group-03.md`: regression hardening and delivery doc synchronization

## ADR

- Accepted: `docs/90-decisions/adr-0017-legacy-cleanup-boundary-and-owner-rename-policy.md`

## Epic Acceptance Target

- Legacy compatibility scaffolding not needed pre-deploy is removed and replaced with one active baseline.
- Bootstrap owner can rename masters; non-owner masters get deterministic deny.
- Rename action is observable (audit events + metrics outcomes) and reflected in user-facing identity texts.
- Local/VM smoke and regression suite remain green after cleanup and rename rollout.
