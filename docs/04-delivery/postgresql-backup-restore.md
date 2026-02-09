# PostgreSQL backup and restore runbook (single VM baseline)

## Scope

This runbook defines the EPIC-007 baseline for logical PostgreSQL backups (`pg_dump` custom format), retention, and restore rehearsal for the `haircuttgbot` stack.

## Prerequisites

- Local stack is running: `docker compose up -d --build`
- Migration job has completed: `docker compose ps -a`
- `postgres` is healthy: `docker compose ps`
- Baseline data is present: `docker compose exec -T bot-api python -m app.db.seed`

## Backup command (logical dump)

1. Create local backup directory:
   `mkdir -p backups/local`
2. Create UTC timestamped dump:
   `TS=$(date -u +%Y%m%dT%H%M%SZ)`
   `docker compose exec -T postgres pg_dump -U haircuttgbot -d haircuttgbot -Fc > "backups/local/haircuttgbot_${TS}.dump"`
3. Verify artifact exists and is non-empty:
   `ls -lh backups/local/haircuttgbot_${TS}.dump`

## Retention baseline

- Keep at least 7 daily dumps on the VM.
- Copy backups off-host daily (object storage or second host) before pruning local copies.
- Example local prune command for files older than 7 days:
  `find backups/local -type f -name 'haircuttgbot_*.dump' -mtime +7 -delete`

## Restore rehearsal (clean state)

1. Capture reference snapshot before destructive restore:
   `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT count(*) AS users_count FROM users; SELECT count(*) AS masters_count FROM masters; SELECT count(*) AS bookings_count FROM bookings; SELECT count(*) AS blocks_count FROM availability_blocks;"`
2. Drop and recreate DB:
   `docker compose exec -T postgres psql -U haircuttgbot -d postgres -c "DROP DATABASE IF EXISTS haircuttgbot WITH (FORCE);"`
   `docker compose exec -T postgres psql -U haircuttgbot -d postgres -c "CREATE DATABASE haircuttgbot OWNER haircuttgbot;"`
3. Restore selected dump:
   `cat backups/local/haircuttgbot_<TIMESTAMP>.dump | docker compose exec -T postgres pg_restore -U haircuttgbot -d haircuttgbot --clean --if-exists --no-owner --no-privileges`
4. Re-run integrity checks:
   `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT count(*) AS users_count FROM users; SELECT count(*) AS masters_count FROM masters; SELECT count(*) AS bookings_count FROM bookings; SELECT count(*) AS blocks_count FROM availability_blocks;"`
5. Validate API health after restore:
   `curl -fsS http://127.0.0.1:8080/health`

## Rehearsal evidence (local)

- Date: 2026-02-09
- Backup artifact created: `backups/local/haircuttgbot_20260209T094803Z.dump`.
- Restore completed to a clean recreated DB.
- Integrity counts matched before/after restore for `users`, `masters`, `bookings`, and `availability_blocks` (`3,2,1,0` before and after).
- `/health` returned `{"status":"ok","service":"bot-api"}` after restore.

## Operational notes

- Run backup at least once per day and before schema migrations.
- Prefer restoring to a temporary database first in production incidents, then switch traffic after validation.
- Do not commit backup artifacts into git.
