# EPIC-025 Tasks

Status legend: TODO / IN_PROGRESS / DONE / BLOCKED.

- T-001 — Finalize ADR for 2-month horizon and paginated date-picker callback contract (window boundaries, page size, stale/edge behavior).  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-002 — Implement shared date-window helper(s) for rolling 2-month bounds in business timezone with deterministic page slicing.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-003 — Add callback state contract for page navigation (`next`/`prev`) with safe token validation and localization baseline.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-004 — Integrate paginated date picker into client booking flow across master/service/date/slot steps for full 2-month horizon.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-005 — Integrate same paginated date picker into master manual booking flow for full 2-month horizon.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-006 — Ensure stale callback/idempotency and guardrail behavior are preserved for page navigation and far-horizon booking attempts.  
  Est: 1 dev-day.  
  PR group: 02.  
  Status: DONE.

- T-007 — Add regression tests for forward/back pagination, first/last page boundaries, and successful far-date booking in client flow.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-008 — Add regression tests for master manual booking with far-date page navigation and unchanged conflict/day-off/lunch checks.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-009 — Synchronize local-dev/deploy-vm runbooks with paginated navigation smoke checks and close doc-sync checklist items.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.
