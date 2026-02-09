# Deployment to a single VM

## Purpose

This document defines the EPIC-008 deployment contract for running the project on one Linux VM with Docker Compose. Detailed step-by-step deploy and rollback commands are completed in later EPIC-008 PR groups.

## VM deployment contract

### Runtime assumptions

- Deployment target is one Linux VM with systemd.
- Docker Engine and Docker Compose v2 are installed on the VM.
- Runtime directory is `/opt/haircuttgbot/current`.
- Persistent PostgreSQL storage is attached as a Docker volume.
- Release switch is atomic by updating a `current` symlink to a versioned release directory.

### Minimum host prerequisites

- OS: Ubuntu 24.04 LTS (or compatible modern Linux distribution).
- CPU/RAM baseline: 2 vCPU, 4 GB RAM, 20 GB free disk.
- Access:
  - SSH access for deploy operator.
  - Docker group privileges for deploy user (or root with sudo).
- Required packages:
  - `docker`
  - `docker compose` plugin
  - `tar`, `curl`, `jq`

### Runtime services

- `bot-api` (FastAPI + Telegram integration logic)
- `postgres` (primary persistence)
- `redis` (cache/state support)
- `migrate` one-shot service (Alembic schema sync before app startup)

### Network and ports

- Inbound:
  - `22/tcp` SSH (restricted by source IP where possible)
  - `80/tcp` optional reverse-proxy HTTP entrypoint
  - `443/tcp` optional reverse-proxy HTTPS entrypoint
- Internal-only (not publicly exposed):
  - `8080/tcp` `bot-api` HTTP (`/health`, `/metrics`, internal endpoints)
  - `5432/tcp` PostgreSQL
  - `6379/tcp` Redis

## Release artifact shape

### Artifact boundaries

Each release is a versioned deploy bundle (example: `haircuttgbot-v2026.02.09.1.tgz`) with:

- `compose.yaml` (runtime service topology)
- `.env.example` (non-secret variable template)
- `deploy/` helper scripts and systemd unit template
- `docs/04-delivery/deploy-vm.md` and smoke-check references

The bundle must not include real secret values.

### VM layout

- `/opt/haircuttgbot/releases/<release-id>/` unpacked release bundle
- `/opt/haircuttgbot/current` symlink to active release
- `/opt/haircuttgbot/shared/.env` environment file with real secrets/config
- `/opt/haircuttgbot/backups/` local PostgreSQL backup storage

## Secrets and configuration strategy

- Real secrets are provisioned only on the VM in `/opt/haircuttgbot/shared/.env`.
- Repository stores only `.env.example` placeholders.
- Secrets never appear in compose files, docs examples, or git history.
- Minimum secret set:
  - `TELEGRAM_BOT_TOKEN`
  - `DATABASE_URL` (if not composed from service defaults)
  - any future third-party API keys

## Operations baseline

- Backup policy: use `pg_dump -Fc` at least daily, keep minimum 7 local copies, and push one daily copy off-host.
- Restore rehearsal: execute runbook from `docs/04-delivery/postgresql-backup-restore.md`.
- Alert policy: apply service-down and booking-failure rules from `docs/04-delivery/alerts-baseline.md`.

## Validation requirements for deploy PR groups

- Deployment docs stay aligned with local runtime assumptions from `docs/04-delivery/local-dev.md`.
- Smoke validation after deploy must include:
  - `/health` and `/metrics` availability
  - client booking success + one-active-booking rejection path
  - master schedule update path (day-off/lunch/manual booking)
- Rollback section must define clear failure triggers and deterministic command path.
