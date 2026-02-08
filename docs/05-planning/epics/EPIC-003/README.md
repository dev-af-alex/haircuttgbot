# EPIC-003 — Telegram auth + role enforcement

Status: DONE

## Goal

Implement Telegram identity resolution and command-level RBAC enforcement for `Client` and `Master` roles.

## Scope

- Telegram user identity lookup from persisted `users`/`roles` tables.
- RBAC checks for protected bot command handlers.
- Structured audit logging for denied commands.
- Russian-language baseline responses for auth/permission scenarios.

## Out of scope

- Full booking command set (handled in EPIC-004/005/006).
- Multi-language support beyond Russian baseline.

## Acceptance criteria

- Telegram user-to-role mapping is resolved from DB for every protected command.
- Unauthorized command attempts are rejected and logged.
- Russian command/menu baseline exists for both roles.

## Dependencies

- EPIC-001 runtime baseline.
- EPIC-002 schema/migrations/seed.

## Delivered

- DB-backed role resolution endpoint (`/internal/auth/resolve-role`).
- RBAC decision endpoint (`/internal/commands/authorize`) with deny logging.
- Russian auth/permission messages for allowed/forbidden/unknown-user paths.
- Automated tests for RBAC decisions and role repository behavior.
