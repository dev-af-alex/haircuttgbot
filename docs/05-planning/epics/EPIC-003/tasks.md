# EPIC-003 tasks

Legend: TODO / IN_PROGRESS / DONE
Sizing target: each task is 1-3 dev-days.

- T-001 — Implement role lookup repository/service — Status: DONE
  - Scope: DB-backed lookup by `telegram_user_id` with strict role mapping.
  - Acceptance:
    - service returns `Client`/`Master` for known users.
    - unknown users are handled explicitly.
  - Estimation: 2 dev-days
  - Dependencies: none

- T-002 — Add RBAC guard for protected bot commands — Status: DONE
  - Scope: central permission check used by command handlers.
  - Acceptance:
    - unauthorized calls are rejected.
    - denial includes structured audit log entry.
  - Estimation: 2 dev-days
  - Dependencies: T-001

- T-003 — Add Russian auth/permission message catalog — Status: DONE
  - Scope: baseline ru messages for unknown user/forbidden command/success prompts.
  - Acceptance:
    - handlers return Russian responses for auth-related cases.
  - Estimation: 1 dev-day
  - Dependencies: T-001

- T-004 — Integrate role checks into minimal command handlers — Status: DONE
  - Scope: wire RBAC into foundational `/start` and role-scoped commands.
  - Acceptance:
    - protected commands validate role before execution.
    - unauthorized attempts are not executed.
  - Estimation: 2 dev-days
  - Dependencies: T-002, T-003

- T-005 — Add tests for identity and RBAC behavior — Status: DONE
  - Scope: unit tests for lookup and authorization paths.
  - Acceptance:
    - tests cover known/unknown users and forbidden command path.
  - Estimation: 1 dev-day
  - Dependencies: T-002, T-004

- T-006 — Final doc-sync and epic acceptance verification — Status: DONE
  - Scope: sync architecture/API/security docs and epic statuses.
  - Acceptance:
    - docs align with implemented auth and RBAC behavior.
  - Estimation: 1 dev-day
  - Dependencies: T-005
