# Security NFR

Mandatory gates (must exist in CI):

- SAST: Bandit (`bandit -q -r app`), PR fails on any reported issue until triaged/fixed.
- Dependency scan: pip-audit (`pip-audit`), PR fails on known vulnerabilities; temporary exceptions require documented ticket and expiry date.
- Secrets scan: Gitleaks (`gitleaks/gitleaks-action@v2`), PR fails on detected secret patterns.

## 1) Threat model (lightweight)

- Assets: booking calendar integrity, role mapping (`Client`/`Master`), bot token, personal schedule data.
- Threat actors: unauthorized Telegram users, compromised master account, malicious bot traffic/spam.
- Primary threats: unauthorized schedule changes, fake bookings/cancellations, token leakage, PII leakage in logs.
- Mitigations: RBAC checks by Telegram user ID, structured-log redaction policy for secret-like fields (`token/secret/password/authorization/api_key/database_url`) plus runtime token masking, and per-user command throttling on Telegram command paths.

## 2) Authentication and authorization

- Auth method: Telegram identity (user ID) + internal role mapping table; no local password auth in MVP.
- Roles/permissions:
  - `Client`: booking flow commands for own bookings only.
  - `Master`: schedule and cancellation commands scoped to own master profile only.
  - Unknown user: no privileged commands; explicit deny response + audit event where applicable.

## 3) Data protection

- In transit:
  - TLS is mandatory at VM ingress (`443/tcp`) via reverse proxy (Nginx/Caddy/Traefik).
  - `80/tcp` only for redirect/challenge flow, not for plaintext API usage.
  - Certificates: Let's Encrypt ACME (auto-renew) or organization-managed certificate with tracked expiry.
- At rest:
  - PostgreSQL data volume stays on encrypted VM disk.
  - Off-host backups are stored encrypted by storage backend or encrypted transport channel.
- Secrets management lifecycle:
  - Source of truth: `/opt/haircuttgbot/shared/.env` on VM only.
  - Repository stores placeholders only (`.env.example`), never real secrets.
  - Rotation minimum: every 90 days and immediately after suspected leakage.
  - Any exposed secret requires immediate revoke/rotate and incident note.

## 4) Auditability

- What to log: role-sensitive actions (booking create/cancel, manual booking, day-off/lunch updates), actor ID, timestamp, result; plus RBAC denials (`rbac_deny`) with telegram user ID, requested command, resolved role, and deny reason.
- What must never be logged: bot token, raw secrets, excessive personal message content.
- Retention:
  - Application/security logs retained 30 days hot on VM.
  - Security-relevant incident extracts retained up to 180 days in restricted storage.
  - Log access limited to operators with production incident responsibilities.

## 5) Abuse prevention

- Rate limiting baseline:
  - Scope: `POST /internal/telegram/*`.
  - Identity keys: `client_telegram_user_id`, `master_telegram_user_id`, `telegram_user_id`.
  - Default policy: `8` requests per `10` seconds per user (`TELEGRAM_THROTTLE_LIMIT`, `TELEGRAM_THROTTLE_WINDOW_SECONDS` env overrides).
  - Deny contract: HTTP `429` with `{"code":"throttled","retry_after_seconds":...}`.
- Bot protection:
  - Structured security event `abuse_throttle_deny` is emitted on limit breach.
  - Metrics expose `bot_api_abuse_outcomes_total{path,outcome}` for operational visibility.
  - Escalation baseline: if one user triggers `>= 20` denies in 15 minutes, create incident note and apply temporary manual block at bot layer (or Telegram allowlist control) for up to 24 hours.
