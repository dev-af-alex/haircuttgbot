# EPIC-022 Tasks

Status legend: TODO / IN_PROGRESS / DONE / BLOCKED.

- T-001 — Finalize ADR for notification identity policy (nickname/phone precedence) and manual-client free-text handling (`adr-0019`).  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-002 — Add/adjust booking data contract for manual client reference text and optional notification contact snapshot fields with deterministic validation.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-003 — Implement repository/service read model for notification context resolution (Telegram nickname, optional phone, manual text fallback, readable slot timestamp).  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-004 — Update master booking-created notification templates and dispatch path to include client context and exact slot date/time.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-005 — Update master manual booking Telegram flow to require/store arbitrary client text and surface it in schedule entries and confirmations.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-006 — Update master-cancel -> client notification payload to include exact cancelled slot date/time while preserving mandatory reason contract.  
  Est: 1 dev-day.  
  PR group: 02.  
  Status: DONE.

- T-007 — Add regression coverage for notification content contracts (master create notify, master cancel notify to client, manual-client text rendering/fallbacks).  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-008 — Add security/observability checks ensuring phone/contact data is masked in logs and notification outcome telemetry remains stable.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.

- T-009 — Sync `local-dev` and `deploy-vm` smoke contracts with manual free-text booking and informative notification validation steps.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.
