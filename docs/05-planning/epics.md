# Epics roadmap (SSOT)

Status values: TODO / IN_PROGRESS / DONE / BLOCKED.

Rules:

- Each epic must keep the system runnable locally via docker-compose.
- Every epic must state acceptance criteria.
- Include deployment to a single VM as a first-class deliverable.

## Epics

- EPIC-001 — Runtime skeleton + CI security gates — Status: DONE
    - Goal: replace placeholder setup with runnable bot-api/postgres/redis skeleton and mandatory CI security checks.
    - Acceptance:
        - `docker compose up -d` starts `bot-api`, `postgres`, and `redis` with health checks.
        - Smoke test in `docs/04-delivery/local-dev.md` is executable and passing.
        - CI runs Bandit, pip-audit, and Gitleaks on pull requests and fails on configured severity threshold.
    - Dependencies: tech stack selected in `docs/03-architecture/tech-stack.md`.
    - Local-run impact: introduces first real local runtime; all next epics build on this compose baseline.
    - Delivered: real compose runtime (`bot-api` + `postgres` + `redis`), health smoke test, and CI baseline with Bandit + pip-audit + Gitleaks.

- EPIC-002 — Data model + migration baseline — Status: DONE
    - Goal: implement relational schema and migrations for roles, masters, clients, bookings, availability blocks, and audit events.
    - Acceptance:
        - Initial DB schema created via migration tooling and applied automatically in local setup.
        - Uniqueness and conflict constraints prevent double-booking for the same master/time slot.
        - Seed data for at least two masters available for local smoke scenarios.
    - Dependencies: EPIC-001.
    - Local-run impact: local `docker compose up -d` provisions a usable database state for bot scenarios.
    - Delivered: Alembic migration baseline, core relational schema + constraints, automatic compose migration job, and seed flow with 2 masters.

- EPIC-003 — Telegram auth + role enforcement — Status: DONE
    - Goal: wire Telegram bot identity and enforce command-level RBAC for `Client` and `Master`.
    - Acceptance:
        - Telegram user ID mapping to role is persisted and validated on every protected command.
        - Unauthorized command attempts are rejected and logged.
        - Russian-language command/menu baseline is available for both roles.
    - Dependencies: EPIC-001, EPIC-002.
    - Local-run impact: local bot interaction now requires role-aware flows and test accounts.
    - Delivered: DB-backed role mapping, RBAC authorization endpoint, ru auth messages, and automated RBAC tests.

- EPIC-004 — Client booking flow — Status: DONE
    - Goal: deliver client journey for viewing availability and creating bookings with service selection.
    - Acceptance:
        - Client can select master and service option (haircut, beard, haircut+beard).
        - Availability excludes occupied slots, day off, and lunch break; default slot duration is 60 minutes.
        - Client is limited to one active future booking and receives confirmation notification.
    - Dependencies: EPIC-002, EPIC-003.
    - Local-run impact: smoke test extends from health checks to end-to-end booking creation via bot.
    - Delivered: service option catalog, availability/read + booking/create flow, Telegram client booking-flow contracts, confirmation notifications, and extended local smoke for success/reject scenarios.

- EPIC-005 — Cancellation and notification flow — Status: DONE
    - Goal: implement cancel scenarios for both roles, including mandatory reason from master.
    - Acceptance:
        - Client can cancel own active booking.
        - Master can cancel client booking only with required textual reason.
        - Cancellation notifications are delivered to affected participants with correct context.
    - Dependencies: EPIC-004.
    - Local-run impact: local smoke covers both client and master cancellation paths.
    - Delivered: client self-cancellation flow, master cancellation with mandatory reason and ownership checks, reasoned cancellation notifications, and updated local smoke coverage for cancel success/reject paths.

- EPIC-006 — Master schedule management — Status: DONE
    - Goal: allow masters to manage schedule directly in Telegram (manual bookings, day off, lunch break updates).
    - Acceptance:
        - Master can create manual booking for off-bot requests.
        - Master can set day-off periods blocking client booking.
        - Default lunch break 13:00-14:00 is enforced and can be changed by master.
    - Dependencies: EPIC-004.
    - Local-run impact: local behavior includes dynamic availability recalculation after master schedule edits.
    - Delivered: master day-off management, lunch-break update flow, manual booking flow with ownership/conflict checks, and updated local smoke coverage for schedule-change scenarios.

- EPIC-007 — Observability + reliability baseline — Status: DONE
    - Goal: add production-ready logging, metrics, backup/restore runbook, and basic alerts for single VM operations.
    - Acceptance:
        - Structured logs include key security and booking lifecycle events without secret leakage.
        - Metrics endpoint exposes health, latency, and booking success/failure counters.
        - Backup and restore procedure for PostgreSQL documented and validated in local/staging rehearsal.
    - Dependencies: EPIC-001, EPIC-002, EPIC-004, EPIC-006.
    - Local-run impact: compose and docs include observability endpoints plus backup/restore rehearsal commands.
    - Delivered: Group 01 structured logs + metrics baseline, Group 02 PostgreSQL backup/restore runbook with local clean-state rehearsal steps, and Group 03 minimal alert baseline + response notes.

- EPIC-008 — Single-VM deployment baseline — Status: DONE
    - Goal: package and deploy the working bot stack onto one VM with documented rollback.
    - Acceptance:
        - `docs/04-delivery/deploy-vm.md` contains complete, reproducible VM deployment and rollback instructions.
        - Production-like compose bundle starts successfully on VM with secrets/config separation.
        - Post-deploy smoke test validates core booking and schedule operations.
    - Dependencies: EPIC-001, EPIC-004, EPIC-006, EPIC-007.
    - Local-run impact: local environment mirrors VM runtime layout to reduce deployment drift.
    - Delivered: Group 01 deployment contract + artifact/secrets strategy and ADR-0005 decision finalization; Group 02 deterministic deploy/rollback runbook with explicit failure triggers; Group 03 post-deploy verification checklist + operational handoff notes and closure sync.

- EPIC-009 — Security and operations hardening baseline — Status: DONE
    - Goal: close remaining MVP NFR gaps for abuse protection, secrets handling, retention policy, and operational SLO definitions on single-VM runtime.
    - Acceptance:
        - Rate-limit and abuse-control baseline is implemented and documented for Telegram-facing command paths.
        - Secret management and TLS ingress policy are fully documented for VM runtime and reflected in delivery docs.
        - SLO/SLI targets and retention policy are defined with alert/runbook alignment.
    - Dependencies: EPIC-007, EPIC-008.
    - Local-run impact: compose runtime remains stable while adding protective middleware/config and updated smoke checks for rejection scenarios.
    - Delivered: Group 01 accepted abuse-protection ADR + Telegram command throttling middleware + abuse observability baseline; Group 02 finalized secrets/TLS/SLO/retention policy docs and deployment-runbook synchronization; Group 03 smoke hardening for throttle rejection and final closure sync.
