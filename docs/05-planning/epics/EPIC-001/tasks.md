# EPIC-001 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Replace placeholder compose with runtime baseline — Status: DONE
  - Scope: define `bot-api`, `postgres`, `redis`, network, volumes, env wiring.
  - Acceptance:
    - `docker compose up -d` starts all services.
    - health checks are defined and visible in `docker compose ps`.
    - no hardcoded secrets in compose file.
  - Estimation: 2 dev-days
  - Dependencies: none

- T-002 — Add minimal bot-api service scaffold — Status: DONE
  - Scope: create minimal FastAPI app, aiogram bootstrap entrypoint, health endpoint.
  - Acceptance:
    - containerized app starts and stays healthy.
    - `/health` endpoint (or equivalent smoke endpoint) returns success.
    - structured logs are emitted on startup.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Define local smoke test and sync local-dev docs — Status: DONE
  - Scope: describe minimal end-to-end local verification and required ports/commands.
  - Acceptance:
    - `docs/04-delivery/local-dev.md` contains explicit smoke test steps.
    - smoke test is runnable on clean checkout after prerequisites.
  - Estimation: 1 dev-day
  - Dependencies: T-001, T-002

- T-004 — Wire CI security gates (Bandit, pip-audit, Gitleaks) — Status: DONE
  - Scope: add CI workflow/jobs and baseline fail policy.
  - Acceptance:
    - PR CI executes all 3 scanners.
    - pipeline fails on findings according to documented policy.
    - scan setup documented in `docs/04-delivery/ci.md`.
  - Estimation: 2 dev-days
  - Dependencies: T-002

- T-005 — Add baseline tests/checks for runtime skeleton — Status: DONE
  - Scope: add lightweight checks to protect local startup and health contract.
  - Acceptance:
    - automated check validates app health endpoint contract.
    - CI runs baseline tests in addition to security scans.
  - Estimation: 1 dev-day
  - Dependencies: T-002

- T-006 — Final doc-sync and epic acceptance verification — Status: DONE
  - Scope: ensure checklists/doc-sync requirements are met for EPIC-001 output.
  - Acceptance:
    - all changed interfaces/workflows reflected in docs.
    - EPIC-001 acceptance checklist is fully mapped to artifacts.
  - Estimation: 1 dev-day
  - Dependencies: T-003, T-004, T-005
