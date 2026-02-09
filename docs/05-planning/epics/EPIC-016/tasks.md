# EPIC-016 tasks

Each task is scoped to 1-3 dev-days and mapped to mergeable PR groups.

| Task ID | Title | Scope | Estimate | Depends on | Planned PR group | Status |
|---|---|---|---|---|---|---|
| T-001 | Finalize guardrail and day-off conflict policy ADR | Define same-day cutoff rule, slot-boundary rounding behavior, and day-off conflict semantics in ADR | 1 day | EPIC-014, EPIC-015 | group-01 | DONE |
| T-002 | Add shared same-day booking boundary helper | Implement reusable helper that filters/normalizes same-day candidate slots to allowed future boundary | 1-2 days | T-001 | group-01 | DONE |
| T-003 | Add day-off conflict validation primitive | Introduce reusable check that rejects day-off creation when active bookings exist for target master/date | 1-2 days | T-001 | group-01 | DONE |
| T-004 | Integrate past-time guardrails into client booking flow | Apply boundary helper in availability + confirmation paths and return localized rejection for stale slot actions | 2-3 days | T-002 | group-02 | DONE |
| T-005 | Integrate day-off rejection into master flow | Wire day-off conflict validation into master callbacks/handlers with readable localized deny message | 1-2 days | T-003 | group-02 | DONE |
| T-006 | Add date-selectable schedule view for master | Extend master schedule menu to choose date and render selected-date schedule in readable format | 2-3 days | EPIC-012, EPIC-015 | group-02 | DONE |
| T-007 | Expand regression tests for guardrails and calendar constraints | Add tests for same-day past-slot rejection, occupied-day day-off rejection, and schedule-by-date behavior | 2-3 days | T-004, T-005, T-006 | group-03 | DONE |
| T-008 | Update local and VM smoke instructions | Add explicit smoke checks for guardrails/day-off/date-view scenarios in delivery docs | 1 day | T-007 | group-03 | DONE |
| T-009 | Epic closure and checklist/doc-sync prep | Verify statuses, synchronize epic artifacts, and prepare close-epic inputs | 1 day | T-008 | group-03 | DONE |

## Notes

- Grouping keeps `docker compose up -d` runnable after each merge.
- Group-01 is foundation-only to minimize risk before user-visible flow wiring.
