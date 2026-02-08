# EPIC-001 — Runtime skeleton + CI security gates

Status: DONE

## Goal

Replace placeholder local setup with a real runnable baseline (`bot-api`, `postgres`, `redis`) and enforce mandatory CI security gates.

## Scope

- Real `docker-compose.yml` for MVP runtime baseline.
- Minimal backend service scaffold (FastAPI + aiogram integration point).
- Health checks and reproducible local smoke test.
- CI pipeline with Bandit, pip-audit, and Gitleaks.
- Documentation sync for local run and CI behavior.

## Out of scope

- Full booking business logic and Telegram command scenarios (handled in later epics).
- VM production deployment hardening (handled in EPIC-008).

## Acceptance criteria

- `docker compose up -d` starts all baseline services and they become healthy.
- Smoke test documented in `docs/04-delivery/local-dev.md` is executable and passes.
- Pull request CI runs Bandit, pip-audit, and Gitleaks and fails on policy breaches.
- Security scan and local-run behavior are reflected in docs.

## Dependencies

- Tech stack fixed in `docs/03-architecture/tech-stack.md`.

## Deliverables

- Compose/runtime files and minimal app skeleton.
- CI workflow files for security gates.
- Updated delivery documentation.

## Delivered

- Real local runtime baseline via `docker-compose` with `bot-api`, `postgres`, and `redis`.
- Health endpoint contract and smoke test procedure.
- CI workflow with `pytest`, Bandit, pip-audit, and Gitleaks.
