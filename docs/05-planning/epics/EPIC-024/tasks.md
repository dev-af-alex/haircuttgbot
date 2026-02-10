# EPIC-024 Tasks

Status legend: TODO / IN_PROGRESS / DONE / BLOCKED.

- T-001 — Define and lock optimization decision in ADR (target queries, index policy, measurement protocol, rollback boundaries).  
  Est: 1 dev-day.  
  PR group: 01.  
  Status: DONE.

- T-002 — Capture baseline for critical booking/schedule query paths (`EXPLAIN ANALYZE` + app-level timings) and store reproducible evidence in docs/artifacts.  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-003 — Build/extend deterministic perf measurement harness for local compose profile (fixed dataset + repeatable command path).  
  Est: 2 dev-days.  
  PR group: 01.  
  Status: DONE.

- T-004 — Implement DB index migrations for identified hotspots (including safe naming and rollback notes).  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-005 — Apply targeted query/service refactors where planner still misses SLA after indexing, preserving functional behavior and timezone semantics.  
  Est: 2 dev-days.  
  PR group: 02.  
  Status: DONE.

- T-006 — Add regression coverage for query correctness and migration safety around optimized paths.  
  Est: 1 dev-day.  
  PR group: 02.  
  Status: DONE.

- T-007 — Validate post-change performance against baseline and confirm p95 <= 600 ms on targeted paths.  
  Est: 2 dev-days.  
  PR group: 03.  
  Status: DONE.

- T-008 — Synchronize `local-dev` and `deploy-vm` docs with performance-check and rollback-safe index verification steps.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.

- T-009 — Finalize merge-gate evidence bundle (tests + perf report + decision/doc sync) for epic closure readiness.  
  Est: 1 dev-day.  
  PR group: 03.  
  Status: DONE.
