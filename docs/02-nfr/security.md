# Security NFR

Mandatory gates (must exist in CI):

- SAST: Bandit (TODO: baseline config and severity threshold).
- Dependency scan: pip-audit (TODO: fail policy and ignorelist process).
- Secrets scan: Gitleaks (TODO: custom rules and baseline handling).

## 1) Threat model (lightweight)

- Assets: booking calendar integrity, role mapping (`Client`/`Master`), bot token, personal schedule data.
- Threat actors: unauthorized Telegram users, compromised master account, malicious bot traffic/spam.
- Primary threats: unauthorized schedule changes, fake bookings/cancellations, token leakage, PII leakage in logs.
- Mitigations: RBAC checks by Telegram user ID, structured-log redaction policy for secret-like fields (`token/secret/password/authorization/api_key/database_url`) plus runtime token masking, and per-user command throttling on Telegram command paths.

## 2) Authentication and authorization

- Auth method: Telegram identity (user ID) + internal role mapping table; no local password auth in MVP.
- Roles/permissions: `Client` and `Master` with strict command-level authorization checks (TODO: final permission matrix).

## 3) Data protection

- In transit: TLS termination for webhook/admin endpoints (TODO: concrete certificate and reverse-proxy setup).
- At rest: TODO (PostgreSQL disk/encryption policy for single VM).
- Secrets management: TODO (inject bot token and DB credentials via environment/secret files, never in repo).

## 4) Auditability

- What to log: role-sensitive actions (booking create/cancel, manual booking, day-off/lunch updates), actor ID, timestamp, result; plus RBAC denials (`rbac_deny`) with telegram user ID, requested command, resolved role, and deny reason.
- What must never be logged: bot token, raw secrets, excessive personal message content.
- Retention: TODO (define log retention window and access policy).

## 5) Abuse prevention

- Rate limiting baseline:
  - Scope: `POST /internal/telegram/*`.
  - Identity keys: `client_telegram_user_id`, `master_telegram_user_id`, `telegram_user_id`.
  - Default policy: `8` requests per `10` seconds per user (`TELEGRAM_THROTTLE_LIMIT`, `TELEGRAM_THROTTLE_WINDOW_SECONDS` env overrides).
  - Deny contract: HTTP `429` with `{"code":"throttled","retry_after_seconds":...}`.
- Bot protection:
  - Structured security event `abuse_throttle_deny` is emitted on limit breach.
  - Metrics expose `bot_api_abuse_outcomes_total{path,outcome}` for operational visibility.
  - Remaining TODO: temporary blocking/escalation policy for repeat offenders.
