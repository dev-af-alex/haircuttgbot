# Tech stack (SSOT)

This document is selected and fixed by **Skill 01 (Bootstrap)**.

## Selected stack

- Backend: Python 3.12, FastAPI, aiogram 3 (polling-first Telegram runtime in one service; webhook mode deferred).
- Frontend (if any): No separate frontend in MVP; Telegram bot UI only.
- Database: PostgreSQL 16.
- Cache/queue: Redis 7 (ephemeral state, throttling, optional job queue).
- Auth provider (if any): Telegram identity (user ID) with internal RBAC mapping.
- Observability: Structured JSON logs + Prometheus metrics endpoint (+ optional Grafana/Loki in later epic).
- CI platform: GitHub Actions.

## Rationale (why this stack)

- Python + aiogram gives fastest path for Telegram-native bot features and handlers.
- FastAPI cleanly supports webhook endpoints, health checks, and future admin/API expansion.
- PostgreSQL is reliable for transactional booking and schedule consistency.
- Redis is simple in docker-compose and helps with rate-limiting/idempotency/session state.
- Single-service backend + compose keeps operations simple for single-VM deployment.
- Security tooling and CI choices are mature and straightforward to automate.

Assumptions:

- Deployment target is one Linux VM with Docker Compose.
- Initial load is small/medium and fits vertical scaling on one VM.
- Users interact via Telegram only in MVP; no standalone web/mobile client required.
- CI/CD repository is hosted on GitHub.

## Containerization model (docker-compose)

- Services: `bot-api` (FastAPI + aiogram), `postgres`, `redis`.
- Networking: one internal compose network; optional reverse proxy for TLS/webhook ingress.
- Volumes: persistent volume for PostgreSQL data; optional volume for logs.
- Config/env: `.env` + secret env vars for bot token and DB credentials (never committed).

## Build/test toolchain

- Build: `docker compose build`.
- Unit tests: `pytest`.
- Integration tests: `pytest` with testcontainers or compose-based integration profile (TODO finalize in implementation epic).
- Lint/format: `ruff` + `black`.

## Security tooling (must be wired in CI)

- SAST tool: Bandit.
- Dependency scan tool: pip-audit.
- Secrets scan tool: Gitleaks.

Related:

- ADR for stack decision: `docs/90-decisions/` (create one when selecting the stack)
