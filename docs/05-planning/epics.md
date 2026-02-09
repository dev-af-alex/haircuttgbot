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

- EPIC-010 — Telegram delivery reliability hardening — Status: DONE
    - Goal: harden Telegram integration for webhook retries, idempotent command handling, and controlled failure behavior under external API constraints.
    - Acceptance:
        - command handling is idempotent for repeated Telegram deliveries in retry windows.
        - webhook/delivery error policy and retry strategy are documented and test-covered.
        - local smoke path includes at least one duplicate-delivery validation scenario.
    - Dependencies: EPIC-003, EPIC-007, EPIC-009.
    - Local-run impact: local compose run remains stable while adding duplicate-delivery guards and retry-oriented observability checks.
    - Delivered: Group 01 delivered accepted delivery-idempotency ADR + Telegram write-path replay guard + baseline replay tests; Group 02 delivered retry/error outcome classification + delivery observability metric/event mapping + duplicate-delivery smoke expansion; Group 03 delivered closure doc-sync and merge-gate readiness checks for epic close-out.

- EPIC-011 — Real Telegram runtime integration (aiogram updates path, command baseline) — Status: DONE
    - Goal: connect aiogram handlers to existing booking/schedule services so the bot can be tested via real Telegram chats, with command-driven baseline interactions.
    - Acceptance:
        - incoming Telegram updates are processed through an implemented runtime path (polling or webhook) in local and VM environments.
        - core role-specific flows (`Client` booking/cancel and `Master` schedule/cancel) are callable from real Telegram interactions.
        - local runbook includes reproducible real Telegram test steps with safe fallback to current internal smoke checks.
    - Dependencies: EPIC-003, EPIC-004, EPIC-005, EPIC-006, EPIC-010.
    - Local-run impact: compose runtime adds bot update processing while preserving existing API/smoke behavior and security gates.
    - Delivered: polling-mode aiogram runtime bootstrap, real Telegram client/master command handlers mapped to existing booking/schedule services, synchronized real Telegram local validation runbook, and epic closure checks with documented pip-audit environment deviation.

- EPIC-012 — Telegram interactive button UX (replace slash-command primary flows) — Status: IN_PROGRESS
    - Goal: move `Client` and `Master` primary journeys from `/` command syntax to interactive inline/reply keyboard flows with callback-driven navigation.
    - Acceptance:
        - Core client journey (master selection, service selection, slot choice, booking create/cancel) is fully executable via interactive buttons without requiring `/` commands.
        - Core master journey (schedule view, day-off, lunch update, manual booking, booking cancellation with reason) is fully executable via interactive buttons without requiring `/` commands.
        - Callback/state handling is idempotent and RBAC-safe; duplicate callbacks and stale menu actions return deterministic, localized (`ru`) responses.
        - Local and VM smoke paths include at least one end-to-end interactive-button scenario for `Client` and `Master`.
    - Dependencies: EPIC-011, EPIC-010, EPIC-009.
    - Local-run impact: local runbook and smoke checks shift from command-centric Telegram validation to button-first scenarios while preserving existing compose runtime and CI security gates.

- EPIC-013 — Bootstrap identity and master administration — Status: DONE
    - Goal: ensure baseline roles and one bootstrap master are always present after migration/startup, with bootstrap master Telegram ID configured via environment and delegated master management rights.
    - Acceptance:
        - On clean DB start, roles required by RBAC are created idempotently by migration/seed path (`Client`, `Master`).
        - One bootstrap master is created or updated by configured Telegram ID (env), and startup fails fast with explicit error if config is missing/invalid.
        - Bootstrap master can add and remove other masters via Telegram button flow with RBAC and audit logging.
        - Local/VM smoke includes bootstrap-role presence and add/remove master scenarios.
    - Dependencies: EPIC-002, EPIC-003, EPIC-011, EPIC-012.
    - Local-run impact: `docker compose up -d` and smoke now require bootstrap master env configuration and verify idempotent baseline seed behavior.
    - Delivered: Group 01 finalized bootstrap provisioning ADR/env contract + idempotent startup seed with fail-fast validation; Group 02 delivered bootstrap-only master add/remove callback flows with audit events and dedicated metrics; Group 03 synchronized local/VM smoke docs, added master-admin regression coverage, and completed closure readiness checks.

- EPIC-014 — Service duration model and variable-slot booking engine — Status: DONE
    - Goal: move from fixed 60-minute slots to per-service durations (for example, haircut 30 min, haircut+beard 60 min) in availability, booking, and conflict checks.
    - Acceptance:
        - Service catalog stores configurable duration per service and default values cover baseline services.
        - Availability generation and conflict detection respect service duration and prevent partial overlap with lunch/day-off/manual bookings.
        - Booking/cancel flows remain idempotent under duplicate Telegram deliveries with variable durations.
        - Smoke tests validate at least one 30-minute and one 60-minute service scenario end-to-end.
    - Dependencies: EPIC-004, EPIC-006, EPIC-010, EPIC-012.
    - Local-run impact: local verification expands from fixed-hour assumptions to mixed-duration slots and updated test fixtures.
    - Delivered: Group 01 service catalog duration model + seed defaults, Group 02 duration-aware availability and shared overlap predicate enforcement, Group 03 interactive callback duration wiring + idempotency regression coverage + mixed-duration smoke/doc synchronization.

- EPIC-015 — Localized readable time and final mobile UX polish — Status: TODO
    - Goal: deliver human-readable time/date messages and complete mobile-first Telegram interaction polish for client/master flows.
    - Acceptance:
        - Client-facing and master-facing booking/schedule messages display slot time in readable localized format (`ru`) instead of raw timestamps.
        - Interactive keyboards keep key options within phone-friendly row widths across main menus and booking/schedule steps.
        - Regression coverage verifies formatting consistency for create/cancel/update notifications.
        - Local/VM smoke includes a real Telegram check for readable time output and phone-usable button menus.
    - Dependencies: EPIC-012, EPIC-013, EPIC-014.
    - Local-run impact: smoke and manual QA checklists add UI/format assertions in addition to API correctness.
