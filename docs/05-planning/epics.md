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

- EPIC-015 — Localized readable time and final mobile UX polish — Status: DONE
    - Goal: deliver human-readable time/date messages and complete mobile-first Telegram interaction polish for client/master flows.
    - Acceptance:
        - Client-facing and master-facing booking/schedule messages display slot time in readable localized format (`ru`) instead of raw timestamps.
        - Interactive keyboards keep key options within phone-friendly row widths across main menus and booking/schedule steps.
        - Regression coverage verifies formatting consistency for create/cancel/update notifications.
        - Local/VM smoke includes a real Telegram check for readable time output and phone-usable button menus.
    - Dependencies: EPIC-012, EPIC-013, EPIC-014.
    - Local-run impact: smoke and manual QA checklists add UI/format assertions in addition to API correctness.
    - Delivered: Group 01 finalized ADR-0012 + shared `ru` formatter and keyboard layout helpers; Group 02 completed client readable booking/cancel texts and client mobile row constraints; Group 03 completed master/admin readable messages, master/admin mobile row constraints, expanded callback regressions, and synchronized local/VM Telegram validation runbooks.

- EPIC-016 — Booking-time guardrails and master calendar constraints — Status: DONE
    - Goal: enforce real-time booking validity and calendar consistency rules for client booking and master day-off operations.
    - Acceptance:
        - Client cannot confirm booking into already-passed time windows; same-day availability starts from the nearest allowed future boundary (for example, at `15:00` only slots from `15:30+` are offered).
        - Master cannot set a day off for a date that already has at least one active booking; bot returns explicit localized rejection.
        - Master can pick an arbitrary target date to view schedule (not only current day), and output remains readable/localized.
        - Regression and smoke coverage include same-day past-slot rejection, day-off rejection on occupied date, and schedule-view-by-date success path.
    - Dependencies: EPIC-006, EPIC-012, EPIC-014, EPIC-015.
    - Local-run impact: local smoke expands with current-time-sensitive checks and master calendar-constraint scenarios.
    - Delivered: Group 01 accepted ADR-0013 + shared same-day boundary helper + day-off conflict primitive; Group 02 integrated stale-slot rejection, occupied-date day-off denial, and schedule-by-date callback flow; Group 03 expanded regression coverage and synchronized local/VM smoke validation steps.

- EPIC-017 — Role-first entry UX and master identity texts — Status: DONE
    - Goal: simplify `/start` and booking UX by removing intermediate main menu and using human-readable master identity across client flows.
    - Acceptance:
        - `Главное меню` section is removed from user-visible navigation; role-resolved users land directly in `Client` or `Master` panel on bot start.
        - `/start` sends barbershop greeting text instead of command-list style response.
        - Client master-selection and booking-confirmation texts show master display name (not `Master ID`) consistently.
        - Regression and smoke coverage validate direct role landing, greeting message contract, and master-name rendering in selection/confirmation flows.
    - Dependencies: EPIC-012, EPIC-013, EPIC-015.
    - Local-run impact: Telegram validation steps in local/VM runbooks shift to role-direct start behavior and updated text assertions.
    - Delivered: Group 01 role-direct `/start` greeting flow + accepted ADR-0014 identity policy; Group 02 master display-name rollout in client selection/confirmation paths with deterministic fallback; Group 03 regression expansion and local/VM runbook synchronization for role-direct start and text contracts.

- EPIC-018 — Manual master assignment by Telegram nickname (`@...`) — Status: DONE
    - Goal: change bootstrap-master administration flow so master assignment is performed by explicit nickname input, not by selecting existing bot users.
    - Acceptance:
        - In `Управление мастерами` add-master flow accepts only manual nickname input starting with `@` and rejects invalid formats.
        - System resolves/stores nickname-based assignment with deterministic behavior when nickname is unknown or ambiguous, with localized operator feedback.
        - Existing add/remove master RBAC and auditability guarantees stay intact.
        - Regression and smoke coverage include success and validation-failure scenarios for nickname-based assignment.
    - Dependencies: EPIC-013, EPIC-017.
    - Local-run impact: local/VM smoke updates bootstrap-master add flow to nickname-first input path and validation checks.
    - Delivered: Group 01 accepted ADR-0015 nickname-resolution policy plus manual nickname-input state and validation baseline; Group 02 delivered nickname-based add-master service/callback integration with bootstrap RBAC and audit reason outcomes preserved; Group 03 delivered regression coverage for success/invalid/unknown/ambiguous nickname paths and synchronized local/VM smoke runbooks.

- EPIC-019 — Auto-registration on bot start + bootstrap-only initial user baseline — Status: DONE
    - Goal: guarantee first contact in Telegram never fails with `Пользователь не найден` by auto-registering users on `/start`, persisting Telegram nickname in DB, and keeping first deployment user seed limited to bootstrap master only.
    - Acceptance:
        - Unknown Telegram user is created idempotently on `/start` with baseline `Client` role, while `BOOTSTRAP_MASTER_TELEGRAM_ID` keeps bootstrap-owner behavior.
        - Telegram nickname is persisted in `users` at registration/start path and used as canonical identity attribute for nickname-based admin flows.
        - Entry flow no longer returns `Пользователь не найден`; restricted actions still return deterministic RBAC deny responses.
        - Fresh deploy baseline contains no pre-created users except the bootstrap master bound to `BOOTSTRAP_MASTER_TELEGRAM_ID`.
        - Local and VM smoke include auto-registration verification for a new Telegram user and bootstrap-only initial-user count validation.
    - Dependencies: EPIC-013, EPIC-017, EPIC-018.
    - Local-run impact: seed/startup contract and smoke assertions shift from demo user pre-provisioning to runtime auto-registration.
    - Delivered: Group 01 finalized ADR-0016 and bootstrap-only seed baseline without demo users; Group 02 delivered idempotent `/start` auto-registration with nickname persistence and no `Пользователь не найден` entry path; Group 03 added regression coverage and synchronized local/VM smoke runbooks for clean baseline and first-user registration checks.

- EPIC-020 — Pre-deploy legacy cleanup + owner-only master rename flow — Status: DONE
    - Goal: remove backward-compatibility code paths not required before first production deploy and add owner-only capability to change master display name.
    - Acceptance:
        - Legacy compatibility branches/adapters that target undeployed historical states are removed; service logic is refactored to one active baseline.
        - Migration/seed/docs are aligned to greenfield-first deployment assumptions without extra compatibility scaffolding.
        - Bootstrap owner master can change another master's display name through Telegram flow; non-owner masters receive deterministic deny.
        - Master rename action is audit-logged and reflected in user-visible booking/schedule texts that show master identity.
        - Regression and smoke coverage include rename success and deny scenarios after legacy cleanup.
    - Dependencies: EPIC-018, EPIC-019.
    - Local-run impact: compose smoke remains runnable while replacing compatibility checks with baseline-flow validations and owner rename checks.
    - Delivered: Group 01 finalized ADR-0017 and removed pre-deploy optional service-type compatibility branches; Group 02 delivered bootstrap-owner-only master rename domain + callback flow with audit/metric outcome reasons; Group 03 added rename/cleanup regressions and synchronized local/VM smoke runbooks.

- EPIC-021 — Configurable business timezone and temporal consistency — Status: DONE
    - Goal: make all booking/schedule time-dependent behavior run in a configurable business timezone (for example, `Europe/Moscow`) while preserving UTC-safe storage and existing guardrail semantics.
    - Acceptance:
        - A required runtime config (for example, `BUSINESS_TIMEZONE`) is introduced with safe default (`Europe/Moscow`) and strict validation against IANA TZ database names.
        - All user-facing times, same-day lead-time guardrails, and date-based schedule calculations are evaluated in business timezone, not host OS timezone.
        - DB persistence remains normalized in UTC (`TIMESTAMPTZ` semantics), with deterministic conversion on read/write boundaries.
        - Regression coverage includes DST-safe behavior (for non-Moscow zones), same-day rejection windows, slot generation, and cancellation/schedule flows under non-UTC timezone config.
        - Local and VM runbooks include timezone config verification and smoke steps that prove configured timezone is active in logs and functional paths.
    - Dependencies: EPIC-014, EPIC-016, EPIC-020.
    - Local-run impact: `.env`/compose contract gains timezone variable; smoke assertions become timezone-aware for date/slot windows and readable time formatting.
    - Delivered: Group 01 accepted ADR-0018 and introduced validated `BUSINESS_TIMEZONE` with shared UTC/business-time helpers; Group 02 switched booking/schedule/callback time semantics to business timezone with UTC persistence boundaries; Group 03 added timezone + DST regression coverage and synchronized local/VM smoke runbooks.

- EPIC-022 — Informative booking/cancellation notifications and manual-client text in master booking — Status: DONE
    - Goal: make booking/cancellation notifications context-rich for both roles and allow master manual booking flow to accept arbitrary client text.
    - Acceptance:
        - Master booking-created notification includes client identity context (Telegram nickname when available, plus phone if present in stored profile/contact data) and exact booking date/time.
        - Client cancellation notification (when cancelled by master) includes exact cancelled booking date/time in readable localized format.
        - Master manual booking flow supports explicit free-text client field (not only existing Telegram user), stores it deterministically, and shows it in master schedule/notification texts.
        - Existing RBAC, cancellation-reason requirement, and readable `ru` datetime formatting remain intact and regression-tested.
    - Dependencies: EPIC-005, EPIC-006, EPIC-015, EPIC-021.
    - Local-run impact: smoke and Telegram validation steps extend to assert richer notification payloads and manual free-text client scenarios.
    - Delivered: notification context data model extension (manual client name + username/phone snapshots), enriched master/client notification texts with exact slot datetime, manual-booking free-text client input in Telegram callbacks, observability phone redaction update, and synchronized SSOT delivery docs with full regression/smoke coverage.

- EPIC-023 — Time-window reminder notifications (2 hours before appointment) — Status: IN_PROGRESS
    - Goal: add proactive reminder notifications for clients exactly for appointments created more than 2 hours before slot start.
    - Acceptance:
        - System schedules and sends reminder to client 2 hours before appointment start in `BUSINESS_TIMEZONE`.
        - If booking is created less than 2 hours before slot start, reminder is not scheduled/sent.
        - Reminder processing is idempotent and resilient to retries/restarts (no duplicate reminders for one booking).
        - Local regression/smoke covers positive reminder case and "no reminder when <2h lead time" case.
    - Dependencies: EPIC-007, EPIC-010, EPIC-021, EPIC-022.
    - Local-run impact: compose runtime gains/remains background scheduler/worker path for reminder dispatch, with deterministic test hooks for time-based validation.

- EPIC-024 — Booking query performance optimization and DB indexing baseline — Status: TODO
    - Goal: reduce slow booking/schedule query paths (currently observed around 1200 ms) via indexing and query-plan optimization with measurable latency improvements.
    - Acceptance:
        - Critical booking/schedule read paths are profiled (`EXPLAIN ANALYZE` and application timing) and top slow queries are documented.
        - Required DB indexes and/or query rewrites are implemented with migration coverage and validated for correctness.
        - p95 latency for targeted critical paths improves from current ~1200 ms baseline to <= 600 ms under defined local load profile.
        - Monitoring and smoke/perf-check docs include repeatable measurement steps and rollback-safe index migration notes.
    - Dependencies: EPIC-002, EPIC-004, EPIC-006, EPIC-007, EPIC-021.
    - Local-run impact: local validation adds repeatable perf-check commands/scenarios in addition to functional smoke, while keeping `docker compose up -d` workflow unchanged.
