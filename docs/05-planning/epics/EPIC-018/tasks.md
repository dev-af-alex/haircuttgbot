# EPIC-018 tasks

Each task is scoped to 1-3 dev-days and mapped to mergeable PR groups.

| Task ID | Title | Scope | Estimate | Depends on | Planned PR group | Status |
|---|---|---|---|---|---|---|
| T-001 | Finalize nickname-resolution ADR | Define format validation, normalization rules, unknown/ambiguous handling, and assignment determinism | 1 day | EPIC-013, EPIC-017 | group-01 | DONE |
| T-002 | Add callback state for manual nickname input | Introduce bounded admin state for awaiting nickname text input in add-master flow | 1-2 days | T-001 | group-01 | DONE |
| T-003 | Implement nickname input validation and localized errors | Enforce leading `@`, allowed characters, and deterministic localized reject messages | 1-2 days | T-001, T-002 | group-01 | DONE |
| T-004 | Implement nickname-based master assignment service path | Resolve nickname to target user/master records and apply add-master action with existing RBAC and audit hooks | 2-3 days | T-001, T-003 | group-02 | DONE |
| T-005 | Wire Telegram admin add flow to manual nickname path | Replace selectable-user add UI in `Управление мастерами` with nickname prompt/confirm interaction | 1-2 days | T-002, T-004 | group-02 | DONE |
| T-006 | Preserve remove-master and backward compatibility checks | Ensure remove flow and bootstrap-only guard remain stable after add-flow refactor | 1 day | T-005 | group-02 | DONE |
| T-007 | Expand regression coverage for nickname assignment | Add tests for success, invalid format, unknown nickname, and ambiguous nickname outcomes | 2-3 days | T-004, T-005, T-006 | group-03 | DONE |
| T-008 | Synchronize local/VM smoke docs for nickname flow | Update runbooks with bootstrap-master nickname-first add validation path | 1 day | T-007 | group-03 | DONE |
| T-009 | Epic closure and checklist/doc-sync prep | Verify status alignment and closure readiness artifacts | 1 day | T-008 | group-03 | DONE |

## Notes

- Grouping keeps `docker compose up -d` runnable after each merge.
- Group-01 isolates policy and input-state groundwork before write-path integration.
