# EPIC-015 tasks

Each task is scoped to 1-3 dev-days and mapped to mergeable PR groups.

| Task ID | Title | Scope | Estimate | Depends on | Planned PR group | Status |
|---|---|---|---|---|---|---|
| T-001 | Finalize readable time + mobile keyboard contract | Define canonical `ru` readable date/time output rules and phone-friendly keyboard width/layout constraints; capture decision in ADR | 1 day | EPIC-012, EPIC-014 | group-01 | DONE |
| T-002 | Implement shared readable-time formatter utility | Add centralized formatter(s) used by bot message templates for slot/date rendering, including deterministic handling for 30/60-minute services | 1-2 days | T-001 | group-01 | DONE |
| T-003 | Add keyboard row-layout helper constraints | Introduce reusable layout helper/settings for row width and action grouping across inline/reply keyboards | 1-2 days | T-001 | group-01 | DONE |
| T-004 | Apply readable formatting to client booking/cancel messages | Replace raw timestamps in client create/cancel/confirmation and slot-pick outputs with shared formatter | 1-2 days | T-002 | group-02 | DONE |
| T-005 | Refactor client interactive keyboards for mobile usability | Update client menu/booking step keyboards to phone-friendly rows without changing flow semantics | 1-2 days | T-003 | group-02 | DONE |
| T-006 | Apply readable formatting to master schedule/update/cancel messages | Update master-facing schedule, day-off/lunch/manual booking, and cancellation reason notifications to shared readable format | 2-3 days | T-002 | group-03 | DONE |
| T-007 | Refactor master/admin keyboards for mobile usability | Update master and bootstrap-master administration keyboards to row-width constraints while preserving RBAC and callback behavior | 1-2 days | T-003 | group-03 | DONE |
| T-008 | Expand regression tests for formatting and layout consistency | Add tests to cover create/cancel/update message formatting and critical keyboard composition expectations for client/master paths | 2-3 days | T-004, T-005, T-006, T-007 | group-03 | DONE |
| T-009 | Sync smoke docs and complete epic closure checks | Update local/VM runbooks with readable-time and mobile-menu checks; complete checklist/doc-sync for epic close | 1 day | T-008 | group-03 | DONE |

## Notes

- Grouping keeps `docker compose up -d` and existing smoke path runnable after each merge.
- Group-01 is intentionally foundation-only (contract + shared utilities) to minimize behavior risk before broad handler updates.
