# EPIC-008 — Single-VM deployment baseline

Status: IN_PROGRESS

## Goal

Package and deploy the working Telegram bot stack onto one Linux VM with reproducible steps, secrets separation, and documented rollback.

## Scope

- Deployment-ready compose baseline for VM runtime.
- Release artifact strategy and deploy procedure for single VM.
- Post-deploy validation path using existing smoke checks.
- Rollback procedure with clear trigger conditions.

## Out of scope

- Multi-node/high-availability architecture.
- Blue/green or canary rollout automation.
- Full infrastructure-as-code provisioning for cloud resources.

## Acceptance criteria

- `docs/04-delivery/deploy-vm.md` contains complete, reproducible VM deployment and rollback instructions.
- Production-like compose bundle starts successfully on VM with secrets/config separation.
- Post-deploy smoke test validates core booking and schedule operations.

## Dependencies

- EPIC-001 runtime baseline.
- EPIC-004 and EPIC-006 business flow smoke coverage.
- EPIC-007 observability/reliability baseline.

## Deliverables

- Finalized deployment runbook for single VM.
- Deployment artifact/layout decision captured by ADR.
- Mergeable rollout plan with smoke validation and rollback checklist.

## Planned PR groups

- Group 01: deployment contract + artifact/secret strategy + ADR.
- Group 02: deploy/rollback command path + runbook hardening.
- Group 03: post-deploy smoke validation checklist + closure sync.

## Notes

- Every PR group must keep local `docker compose` workflow operational.
- Merge method remains merge-commit per repository policy.
