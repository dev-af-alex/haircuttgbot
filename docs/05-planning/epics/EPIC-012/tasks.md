# EPIC-012 tasks

Legend:
- Size: S (<=1 dev-day), M (1-2 dev-days), L (2-3 dev-days)
- Status: TODO / IN_PROGRESS / DONE / BLOCKED

## Task list

- T-001 (M) - Define button UX map and callback contract per role - Status: DONE
  - Output: role menus, callback payload schema, stale-action rules, localization keys.
  - Acceptance checks:
    - UX map covers all existing command-baseline journeys for `Client` and `Master`.
    - Callback contract documents payload bounds, action names, and backward-compatibility strategy.
  - Dependencies: none
  - PR group: group-01

- T-002 (M) - Implement shared callback router + state guard layer - Status: DONE
  - Output: aiogram callback router, payload validation, stale-action detection, deterministic error replies.
  - Acceptance checks:
    - Invalid/stale callback actions produce stable `ru` user messages and audit log event.
    - Duplicate callback deliveries remain idempotent on write paths.
  - Dependencies: T-001
  - PR group: group-01

- T-003 (M) - Implement Client interactive booking flow - Status: DONE
  - Output: button-first client flow (master -> service -> date/time -> confirm/cancel) reusing existing booking services.
  - Acceptance checks:
    - Client booking create/cancel works without `/` commands.
    - One-active-booking limit and availability conflict rules are preserved.
  - Dependencies: T-002
  - PR group: group-02

- T-004 (L) - Implement Master interactive schedule/cancel flows - Status: DONE
  - Output: button-first master flow for schedule view, day-off, lunch update, manual booking, cancellation with reason.
  - Acceptance checks:
    - Master paths are RBAC-scoped to own profile and preserve business validations.
    - Cancellation reason remains mandatory and delivered to client.
  - Dependencies: T-002
  - PR group: group-03

- T-005 (S) - Update tests and smoke coverage for button scenarios - Status: DONE
  - Output: unit/integration tests for callback handlers and deterministic stale-action responses.
  - Acceptance checks:
    - CI test path remains green with added callback-flow coverage.
    - Existing internal API smoke path is preserved.
  - Dependencies: T-003, T-004
  - PR group: group-03

- T-006 (S) - Synchronize local/VM docs for interactive validation - Status: DONE
  - Output: updated runbook notes for real Telegram button checks in local and VM docs.
  - Acceptance checks:
    - `docs/04-delivery/local-dev.md` includes button-first real Telegram validation steps.
    - `docs/04-delivery/deploy-vm.md` post-deploy verification mentions interactive flow checks.
  - Dependencies: T-003, T-004
  - PR group: group-03

## PR groups overview

- group-01: design contract + callback routing foundation (mergeable without breaking current command paths)
- group-02: client interactive flows
- group-03: master interactive flows + tests + docs sync
