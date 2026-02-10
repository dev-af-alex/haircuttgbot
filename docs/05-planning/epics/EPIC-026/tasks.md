# EPIC-026 Tasks

Status legend: TODO / IN_PROGRESS / DONE / BLOCKED.

- T-001 — Finalize grouped-booking ADR and callback contract (participant identity, organizer ownership rules, participant-level cancellation semantics).  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-002 — Add grouped booking data model primitives for request-level grouping and participant-level linkage without breaking existing booking/cancel contracts.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-003 — Define callback/menu state contract for participant add/edit progression and deterministic stale handling.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-004 — Implement client grouped participant creation flow with required participant-name input and independent master/service/date/slot selection per participant.  
  Est: 3 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-005 — Preserve existing guardrails and ownership constraints while allowing multi-participant grouped booking composition in one organizer session.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-006 — Add participant-aware notification context for grouped booking confirmations without exposing extra PII beyond existing policy.  
  Est: 1 dev-day.  
  PR group: 02.  
  Status: DONE.

- T-007 — Implement participant-level cancellation flow for grouped bookings (no full-group bulk cancel) with deterministic texts.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-008 — Add regression coverage for grouped multi-master/multi-day creation, participant-level cancellation, and unchanged `FR-017` organizer policy.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-009 — Synchronize local-dev/deploy-vm smoke and SSOT docs for grouped create/cancel validation scenarios.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.
