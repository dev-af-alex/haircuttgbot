# EPIC-014 tasks

Each task is scoped to 1-3 dev-days and mapped to mergeable PR groups.

| Task ID | Title | Scope | Estimate | Depends on | Planned PR group | Status |
|---|---|---|---|---|---|---|
| T-001 | Add service duration to catalog model and seed defaults | Migration/model update for service duration field, domain validation (>0), seed defaults for baseline services | 1-2 days | EPIC-002 baseline schema | group-01 | DONE |
| T-002 | Introduce duration-aware availability slot generator | Refactor availability builder to evaluate slot fit by requested service duration and working-window boundaries | 2-3 days | T-001 | group-02 | DONE |
| T-003 | Enforce interval overlap checks for booking/schedule writes | Centralize overlap predicate for bookings, manual bookings, lunch and day-off intervals with variable durations | 2-3 days | T-001 | group-02 | DONE |
| T-004 | Wire duration selection through interactive client flow | Ensure callback/menu flow passes selected service duration through date/slot selection and confirmation | 1-2 days | T-001, T-002 | group-03 | DONE |
| T-005 | Preserve idempotent booking/cancel behavior with variable durations | Extend replay/idempotency handling and duplicate callback behavior for variable-duration booking commands | 1-2 days | T-002, T-003 | group-03 | DONE |
| T-006 | Expand automated tests for 30/60 minute scenarios | Add repository/service/API/callback regression tests for overlaps, boundary slots, and duplicate deliveries | 2-3 days | T-002, T-003, T-005 | group-03 | DONE |
| T-007 | Update local and VM smoke documentation | Add canonical mixed-duration smoke checks to local-dev and deploy verification docs | 1 day | T-004, T-006 | group-03 | DONE |
| T-008 | Epic closure and doc-sync checks | Run checklist gates, close open task statuses, and sync epic README/tasks/pr-group artifacts | 1 day | T-007 | group-03 | DONE |

## Notes

- Grouping keeps `docker compose up -d` path working after each merge.
- Group-01 is schema-safe and backward compatible before enabling variable-duration behavior.
