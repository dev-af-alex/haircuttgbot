# EPIC-021 Tasks

Status legend: TODO / IN_PROGRESS / DONE / BLOCKED.

- T-001 — Finalize ADR for configurable business timezone policy and UTC boundary contract (`adr-0018`).  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-002 — Add runtime timezone config (`BUSINESS_TIMEZONE`) with strict IANA validation and fail-fast startup checks.  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-003 — Introduce shared timezone helper primitives for UTC<->business-time conversions and business-date derivation.  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-004 — Refactor booking guardrails and availability calculations to evaluate same-day windows in business timezone.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-005 — Refactor schedule/day-off/lunch/manual booking flows to use business-date semantics with UTC-safe persistence.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-006 — Align Telegram presentation/formatting and callback flows with configured business timezone outputs.  
  Est: 1 dev-day.  
  PR group: 02.  
  Status: DONE.

- T-007 — Add regression coverage for timezone config, conversion boundaries, and same-day guardrails under non-UTC timezone.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-008 — Add regression coverage for DST-sensitive zones (for example, `Europe/Berlin`) while keeping Moscow path stable.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.

- T-009 — Sync `local-dev` and `deploy-vm` smoke contracts with timezone configuration and verification steps.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.
