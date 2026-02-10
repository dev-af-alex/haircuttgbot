# EPIC-023 Tasks

Status legend: TODO / IN_PROGRESS / DONE / BLOCKED.

- T-001 — Finalize ADR for reminder scheduling policy (eligibility, timing boundary, retry/idempotency semantics) (`adr-0020`).  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-002 — Add/adjust reminder persistence contract (state/status, due timestamp, sent marker, booking linkage) with migration coverage.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-003 — Implement reminder eligibility resolver: schedule only when booking is created >= 2 hours before slot start in business timezone.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-004 — Implement background reminder polling/scheduler worker in compose runtime with safe start/stop behavior.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-005 — Integrate reminder dispatch into Telegram delivery path with idempotent send contract and deterministic outcome recording.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-006 — Add observability for reminder lifecycle (scheduled/skipped/sent/replayed/failed) and align retry behavior with existing delivery policy.  
  Est: 1 dev-day.  
  PR group: 02.  
  Status: DONE.

- T-007 — Add regression coverage for positive reminder case (>=2h lead) and skip case (<2h lead), including timezone-aware boundary checks.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-008 — Add failure/restart regression tests proving no duplicate reminder sends for one booking under replay/retry scenarios.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-009 — Sync `local-dev` and `deploy-vm` smoke contracts with reminder validation steps and operational verification commands.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.
