# ADR-0021: Booking query performance and indexing strategy

Date: 2026-02-10
Status: Accepted
Deciders: Backend maintainers

## Context

Critical booking/schedule query paths are observed around ~1200 ms at p95 under current local profile. The project needs deterministic, measurable performance improvements without changing user-facing behavior or breaking deployment safety.

## Decision

- Profile first, optimize second: use reproducible baseline (`EXPLAIN ANALYZE` + app-level timings) for top query paths.
- Prefer additive, rollback-safe index migrations before intrusive query rewrites.
- Optimize for dominant predicates in booking/schedule paths:
  - `bookings` by (`master_id`, `status`, `slot_start`) and (`client_user_id`, `status`, `slot_start`);
  - partial active-slot overlap index on `bookings` (`master_id`, `slot_start`, `slot_end`) for `status='active'`;
  - `availability_blocks` overlap/day-window indexes by (`master_id`, `start_at`, `end_at`) plus day-off partial variant;
  - pending reminder dispatch index on `booking_reminders` (`due_at`, `id`) for `status='pending'`;
  - functional nickname lookup index on `users` via `lower(telegram_username)`.
- Keep time semantics (`BUSINESS_TIMEZONE` UI + UTC persistence) and existing booking correctness constraints unchanged.
- For partial-index selectivity, use literal `status='active'` in hotspot queries where the status is invariant.
- Accept optimization only with measurable p95 improvement and regression-safe test coverage.

## Alternatives considered

- Immediate query rewrites without baseline profiling.  
  Rejected: high risk of non-deterministic gains and regressions.
- Infrastructure scaling only (larger VM) without DB/query optimization.  
  Rejected: increases cost and does not address root query inefficiencies.
- Caching-heavy approach for dynamic booking availability.  
  Rejected: stale-data risk and higher invalidation complexity for MVP.

## Consequences

- Requires repeatable perf measurement workflow in local/VM docs.
- Introduces migration and planner-review discipline before merge.
- Keeps optimization scope constrained to schema/query changes that preserve current contracts.
