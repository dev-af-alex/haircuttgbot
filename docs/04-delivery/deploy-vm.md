# Deployment to a single VM

## Purpose

This document defines the deployment contract and the reproducible command path for deploying and rolling back the project on one Linux VM with Docker Compose.

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
- Secrets rotation baseline:
  - rotate `TELEGRAM_BOT_TOKEN` and other external API credentials at least every 90 days;
  - rotate immediately after any suspected exposure;
  - after rotation, restart services and verify `/health`, `/metrics`, and smoke checks.
- Minimum secret set:
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_UPDATES_MODE` (`polling` default in current baseline; `disabled` for maintenance windows)
  - `DATABASE_URL` (if not composed from service defaults)
  - any future third-party API keys

## TLS ingress baseline

- Public ingress to bot API must terminate TLS on reverse proxy (Nginx/Caddy/Traefik).
- `443/tcp` is required for webhook/admin ingress; `80/tcp` should only be used for redirect or ACME challenge.
- TLS certificate source:
  - Let's Encrypt ACME with automatic renewal, or
  - organization-managed certificate with tracked expiration/renewal owner.
- Internal compose services (`8080`, `5432`, `6379`) remain non-public and reachable only on private host network paths.

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

## Deployment runbook (clean VM -> running stack)

### Inputs

- `RELEASE_ID` (example: `v2026.02.09.2`)
- `BUNDLE` filename (example: `haircuttgbot-v2026.02.09.2.tgz`)
- SSH target host and deploy user

### 1. Prepare host packages and directories

Run on VM as deploy user with sudo privileges:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin tar curl jq
sudo usermod -aG docker "$USER"

sudo mkdir -p /opt/haircuttgbot/releases
sudo mkdir -p /opt/haircuttgbot/shared
sudo mkdir -p /opt/haircuttgbot/backups
sudo chown -R "$USER":"$USER" /opt/haircuttgbot
```

Re-login once after adding the user to `docker` group.

### 2. Provision runtime secrets (VM only)

Create `/opt/haircuttgbot/shared/.env` from the template values:

```bash
cat >/opt/haircuttgbot/shared/.env <<'ENV'
TELEGRAM_BOT_TOKEN=replace_me
TELEGRAM_UPDATES_MODE=polling
# Optional when defaults are overridden:
# DATABASE_URL=postgresql+psycopg://haircuttgbot:haircuttgbot@postgres:5432/haircuttgbot
ENV
chmod 600 /opt/haircuttgbot/shared/.env
```

### 3. Upload and unpack the release bundle

Run from operator machine:

```bash
scp "$BUNDLE" deploy@<vm-host>:/tmp/
```

Run on VM:

```bash
export RELEASE_ID="v2026.02.09.2"
export BUNDLE="haircuttgbot-v2026.02.09.2.tgz"
export RELEASE_DIR="/opt/haircuttgbot/releases/${RELEASE_ID}"

mkdir -p "$RELEASE_DIR"
tar -xzf "/tmp/${BUNDLE}" -C "$RELEASE_DIR"
```

### 4. Activate release and start services

Run on VM:

```bash
ln -sfn "$RELEASE_DIR" /opt/haircuttgbot/current
cd /opt/haircuttgbot/current

docker compose --env-file /opt/haircuttgbot/shared/.env up -d
docker compose --env-file /opt/haircuttgbot/shared/.env ps -a
```

Expected state:

- `migrate` is `Exited (0)`.
- `bot-api`, `postgres`, and `redis` are `healthy`.

### 5. Post-deploy verification

Run on VM:

```bash
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_service_health|bot_api_requests_total|bot_api_request_latency_seconds|bot_api_booking_outcomes_total|bot_api_abuse_outcomes_total'
docker compose --env-file /opt/haircuttgbot/shared/.env logs bot-api --tail=50 | grep '"event": "startup"'
```

Then run the canonical smoke path from `docs/04-delivery/local-dev.md` against VM services (seed + booking/cancellation/schedule scenario).

### 6. Persist on reboot (systemd)

Use one-shot unit that runs compose up from `/opt/haircuttgbot/current`:

```ini
[Unit]
Description=haircuttgbot compose runtime
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/haircuttgbot/current
RemainAfterExit=yes
ExecStart=/usr/bin/docker compose --env-file /opt/haircuttgbot/shared/.env up -d
ExecStop=/usr/bin/docker compose --env-file /opt/haircuttgbot/shared/.env down

[Install]
WantedBy=multi-user.target
```

Save as `/etc/systemd/system/haircuttgbot.service`, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now haircuttgbot.service
sudo systemctl status haircuttgbot.service --no-pager
```

## Rollback runbook

### Rollback triggers (must be explicit)

Trigger rollback when any of the following is true after deploy:

- `docker compose ps -a` shows unhealthy/failed runtime services after startup grace period.
- `curl -fsS http://127.0.0.1:8080/health` fails.
- Smoke scenario from `docs/04-delivery/local-dev.md` fails.
- Critical dependency break blocks booking or schedule write paths.

### Rollback command path

Run on VM:

```bash
cd /opt/haircuttgbot/releases
ls -1dt v*/ | head -n 5
```

Select previous known-good release as `PREV_RELEASE_ID`, then:

```bash
export PREV_RELEASE_ID="v2026.02.09.1"
export PREV_DIR="/opt/haircuttgbot/releases/${PREV_RELEASE_ID}"

ln -sfn "$PREV_DIR" /opt/haircuttgbot/current
cd /opt/haircuttgbot/current
docker compose --env-file /opt/haircuttgbot/shared/.env up -d
docker compose --env-file /opt/haircuttgbot/shared/.env ps -a
```

### Rollback validation

Run the same minimum checks as forward deploy:

```bash
curl -fsS http://127.0.0.1:8080/health
curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_service_health|bot_api_requests_total|bot_api_request_latency_seconds|bot_api_booking_outcomes_total|bot_api_abuse_outcomes_total'
```

Then execute canonical smoke checks from `docs/04-delivery/local-dev.md`.

### Incident note requirement

Every rollback must produce a short incident note with:

- Failed release ID and timestamp (UTC).
- Trigger condition that caused rollback.
- Rollback operator and restored release ID.
- Health/smoke verification result after rollback.

## Post-deploy verification checklist (release gate)

Use this checklist after every production deployment and rollback recovery.

### Service and observability checks

- `docker compose --env-file /opt/haircuttgbot/shared/.env ps -a` shows:
  - `migrate` finished with `Exited (0)`
  - `bot-api`, `postgres`, `redis` are healthy
- `curl -fsS http://127.0.0.1:8080/health` returns `{"status":"ok","service":"bot-api"}`
- `curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_service_health|bot_api_requests_total|bot_api_request_latency_seconds|bot_api_booking_outcomes_total|bot_api_abuse_outcomes_total'` returns expected metric families
- `docker compose --env-file /opt/haircuttgbot/shared/.env logs bot-api --tail=50 | grep '"event": "startup"'` returns startup structured log

### Functional smoke checks

Run canonical smoke steps from `docs/04-delivery/local-dev.md`:

- seed baseline data
- booking flow success + one-active-booking rejection
- client cancellation + master cancellation-without-reason rejection
- master day-off update
- master lunch update
- master manual booking success + overlap rejection

### Handoff notes for operations

- Record deployed release ID and UTC deployment timestamp.
- Attach results of the post-deploy checklist to change/incident ticket.
- Document whether rollback was needed; if yes, include rollback incident note from section above.
- Confirm backup job status and most recent successful dump in `/opt/haircuttgbot/backups/`.
- Confirm alert routes are active for service-down and booking-failure spike signals.

### Linked runbooks

- Local smoke/reference checks: `docs/04-delivery/local-dev.md`
- Backup/restore rehearsal: `docs/04-delivery/postgresql-backup-restore.md`
- Alert baseline and triage: `docs/04-delivery/alerts-baseline.md`
