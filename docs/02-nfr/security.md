# Security NFR

Mandatory gates (must exist in CI):

- SAST: Bandit (TODO: baseline config and severity threshold).
- Dependency scan: pip-audit (TODO: fail policy and ignorelist process).
- Secrets scan: Gitleaks (TODO: custom rules and baseline handling).

## 1) Threat model (lightweight)

- Assets: booking calendar integrity, role mapping (`Client`/`Master`), bot token, personal schedule data.
- Threat actors: unauthorized Telegram users, compromised master account, malicious bot traffic/spam.
- Primary threats: unauthorized schedule changes, fake bookings/cancellations, token leakage, PII leakage in logs.
- Mitigations: TODO (RBAC checks by Telegram user ID, secure secret storage, audit logging, rate limiting, input validation).

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

- Rate limiting: TODO (per-user command throttling and webhook burst controls).
- Bot protection: TODO (unknown-user command handling, abuse detection, temporary blocking rules).
