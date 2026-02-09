# EPIC-019 Tasks

Status legend: TODO / IN_PROGRESS / DONE / BLOCKED.

- T-001 — Finalize auto-registration and bootstrap-only seed ADR (`adr-0016`).  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-002 — Refactor bootstrap seed/startup path to create only required roles plus bootstrap owner user/master on clean DB.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-003 — Implement idempotent `/start` auto-registration for unknown users with baseline `Client` role assignment.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-004 — Persist Telegram nickname in registration/start path and remove `Пользователь не найден` start-entry branch.  
  Est: 1 dev-day.  
  PR group: 02.  
  Status: DONE.

- T-005 — Add/extend automated tests for bootstrap-only baseline, `/start` auto-registration idempotency, and nickname persistence.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-006 — Sync `local-dev` and `deploy-vm` smoke contracts to new baseline and registration checks.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.
