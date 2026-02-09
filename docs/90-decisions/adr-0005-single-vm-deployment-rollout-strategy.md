# ADR-0005: Single-VM deployment rollout strategy baseline

Date: 2026-02-09
Status: Accepted
Deciders: Engineering

## Context

EPIC-008 requires a reproducible deployment and rollback baseline for a single Linux VM. We need a default release transport and rollback strategy that fits the current docker-compose architecture, keeps operational complexity low, and avoids introducing secrets into repository artifacts.

## Decision

Use a versioned compose bundle deployed on-VM with a shared secrets file and symlink-based release switching.

- Release artifact is a versioned tarball containing `compose.yaml`, helper deploy assets, and `.env.example`.
- On VM, each release is unpacked to `/opt/haircuttgbot/releases/<release-id>/`.
- Active deployment is controlled by `/opt/haircuttgbot/current` symlink.
- Real secrets live only in `/opt/haircuttgbot/shared/.env` and are referenced at runtime.
- Deploy/rollback path uses deterministic `docker compose` commands executed from the active release directory.

## Alternatives considered

- Build/pull container image directly from registry on VM without versioned compose bundle.
- Full configuration-management approach (Ansible/Terraform + remote orchestration).
- Ad-hoc manual container restart process without formal release artifact.

## Consequences

### Positive

- Keeps release process simple and auditable for a single-VM scope.
- Enables low-friction rollback by switching to a previous release directory.
- Prevents secret leakage into git-tracked files by hard-separating runtime secret storage.
- Aligns with existing docker-compose local/runtime model to reduce environment drift.

### Negative

- Requires strict VM filesystem discipline (`releases/`, `current`, `shared`) by operators.
- Without a registry-first pipeline, bundle distribution and retention must be managed explicitly.
- Symlink-based rollout still needs careful health/smoke gating to avoid promoting broken releases.

### Follow-up actions

- EPIC-008 Group 02 will codify exact deploy/rollback commands in `docs/04-delivery/deploy-vm.md`.
- EPIC-008 Group 03 will add post-deploy checklist and closure validation tied to smoke tests.
