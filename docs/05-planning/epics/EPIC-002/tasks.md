# EPIC-002 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Add migration toolchain and bootstrap migration — Status: DONE
  - Scope: configure Alembic (or equivalent) and create first migration execution path.
  - Acceptance:
    - migration command runs against local Postgres.
    - base migration folder and env config are committed.
    - compose startup documents migration application strategy.
  - Estimation: 2 dev-days
  - Dependencies: none

- T-002 — Define core schema entities and constraints — Status: DONE
  - Scope: roles/users/masters/bookings/availability_blocks/audit_events tables.
  - Acceptance:
    - schema includes required PK/FK/unique constraints.
    - booking uniqueness prevents conflicting slot for one master.
    - schema docs updated.
  - Estimation: 3 dev-days
  - Dependencies: T-001

- T-003 — Add seed data for local smoke scenarios — Status: DONE
  - Scope: seed at least two masters and minimal reference data.
  - Acceptance:
    - seed command/script is reproducible.
    - local smoke can rely on seeded masters.
  - Estimation: 1 dev-day
  - Dependencies: T-002

- T-004 — Wire migrations into local compose lifecycle — Status: DONE
  - Scope: ensure migrations run before app readiness in local stack.
  - Acceptance:
    - `docker compose up -d --build` produces schema-ready database.
    - failure path is visible in logs and non-zero exit code.
  - Estimation: 2 dev-days
  - Dependencies: T-001, T-002

- T-005 — Add schema regression checks in CI — Status: DONE
  - Scope: add automated checks for migration validity and model consistency.
  - Acceptance:
    - CI runs migration checks.
    - breaking schema changes are caught before merge.
  - Estimation: 1 dev-day
  - Dependencies: T-002

- T-006 — Final doc-sync and epic acceptance verification — Status: DONE
  - Scope: sync architecture/data/local-dev docs and task statuses.
  - Acceptance:
    - docs match delivered migration/model behavior.
    - EPIC-002 acceptance map is complete.
  - Estimation: 1 dev-day
  - Dependencies: T-003, T-004, T-005
