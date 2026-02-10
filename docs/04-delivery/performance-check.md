# Performance check runbook (EPIC-024)

## Purpose

Provide a repeatable way to measure booking/schedule query latency before and after index/query optimizations.

## Preconditions

- Local stack is running and healthy:
  - `docker compose up -d --build`
  - `docker compose exec -T bot-api python -m app.db.seed`
  - `curl -fsS http://127.0.0.1:8080/health`
- Migrations are at head.

## Profiling command

Run from project root:

- `DATABASE_URL=postgresql+psycopg2://${POSTGRES_USER:-haircuttgbot}:${POSTGRES_PASSWORD:-haircuttgbot}@127.0.0.1:5432/${POSTGRES_DB:-haircuttgbot} .venv/bin/python scripts/perf/profile_booking_queries.py --iterations 200`

Output report is written to:

- `docs/05-planning/epics/EPIC-024/perf-report.md`

## Target and interpretation

- Target for EPIC-024: p95 <= `600 ms` for profiled critical booking/schedule reads.
- Compare p95 values and `EXPLAIN (ANALYZE, BUFFERS)` plans between baseline and post-index runs.
- If p95 target is not met:
  - verify migrations/indexes applied;
  - inspect slowest query plans in report;
  - apply additional query-level changes only after preserving behavior tests.

## Rollback-safe index verification

Validate applied indexes on PostgreSQL:

- `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND (indexname LIKE 'ix_bookings_%' OR indexname LIKE 'ix_availability_blocks_%' OR indexname LIKE 'ix_booking_reminders_%' OR indexname = 'ix_users_lower_telegram_username') ORDER BY indexname;"`

If rollback is required, use deployment rollback path in `docs/04-delivery/deploy-vm.md` and apply alembic downgrade/rollback migration plan for affected release.
