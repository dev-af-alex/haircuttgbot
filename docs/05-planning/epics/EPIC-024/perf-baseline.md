# EPIC-024 Baseline Notes

## Baseline source

- Product request context before EPIC-024 implementation reported booking/schedule queries around `~1200 ms`.
- This value is treated as the pre-optimization p95 baseline for targeted hotspots in this epic.

## Baseline query inventory

- Availability read for active bookings in day window by master.
- Availability read for blocking intervals in day window by master.
- Client future-active booking existence guard.
- Master future-active booking list (`ORDER BY slot_start LIMIT 20`).

## Measurement contract

- Reproducible profiling command and report format are defined in:
  - `scripts/perf/profile_booking_queries.py`
  - `docs/04-delivery/performance-check.md`
- Post-change measurements are stored in:
  - `docs/05-planning/epics/EPIC-024/perf-report.md`
