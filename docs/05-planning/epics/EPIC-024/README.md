# EPIC-024 — Booking query performance optimization and DB indexing baseline

Status: DONE
Started: 2026-02-10
Roadmap source: `docs/05-planning/epics.md`

## Goal

Reduce slow booking/schedule query paths (currently around 1200 ms) by introducing profile-driven indexing and query-plan optimizations with measurable latency gains.

## Scope

- Profile critical booking/schedule reads using SQL-level plans and application timing.
- Implement index/query changes via migrations and bounded query refactors.
- Verify latency improvement against repeatable local load/measurement steps.
- Keep docker-compose local run and VM deploy path unchanged and runnable.

## Out of Scope

- Functional UX changes in Telegram flows.
- New infrastructure components beyond current stack.
- Cross-service architectural changes not needed for query performance.

## Dependencies

- EPIC-002 (schema/migrations baseline)
- EPIC-004 (booking flow)
- EPIC-006 (master schedule management)
- EPIC-007 (observability)
- EPIC-021 (business timezone consistency)

## Planned PR Groups

- `group-01.md`: baseline profiling + optimization ADR + target query inventory
- `group-02.md`: index and query-plan improvements via migrations/service changes
- `group-03.md`: perf regression validation + runbook/doc synchronization

## ADR

- Accepted: `docs/90-decisions/adr-0021-booking-query-performance-indexing-strategy.md`

## Delivery Note

- 2026-02-10: Implemented index-focused optimization baseline (`20260210_0006`), literal-active hotspot query alignment, perf profiling harness (`scripts/perf/profile_booking_queries.py`), and synchronized performance runbooks.
- Profiling evidence recorded in `docs/05-planning/epics/EPIC-024/perf-report.md`; app-level p95 stayed below `600 ms` for targeted booking/schedule read paths in the defined local synthetic profile.
- Baseline reference captured in `docs/05-planning/epics/EPIC-024/perf-baseline.md`.

## Epic Acceptance Target

- Critical booking/schedule read paths are documented with baseline measurements and query plans.
- Migrations introduce validated indexes (or query rewrites) that preserve behavior correctness.
- p95 latency for targeted critical paths improves from ~1200 ms to <= 600 ms in defined local profile.
- Local and VM delivery docs include repeatable performance verification commands and rollback-safe notes.
