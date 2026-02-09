# EPIC-014 — PR Group 01

## Objective

Establish duration-capable service catalog persistence with backward-compatible defaults, without changing runtime booking behavior yet.

## Scope

- Add DB schema support for service duration (minutes) on service catalog records.
- Add domain-level validation for allowed duration values (>0, integer minutes).
- Update seed/bootstrap path to ensure baseline services have explicit duration values.
- Keep existing fixed-duration booking logic unchanged in this group.

## Tasks included

- T-001 Add service duration to catalog model and seed defaults - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable by merge commit independently.
- `docker compose up -d --build` remains healthy (`migrate` exit 0; `bot-api`, `postgres`, `redis` healthy).
- Existing booking/callback smoke path must still pass with no behavior regression.

## Acceptance checks

1. Apply migrations in local compose and verify healthy state:
   - `docker compose up -d --build`
   - `docker compose ps -a`
2. Validate service catalog schema contains duration field and seeded values:
   - `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT code, duration_minutes FROM services ORDER BY code;"`
3. Run targeted tests covering model validation and seed idempotency:
   - `.venv/bin/pytest -q` (targeted test modules for service catalog/migrations)
4. Run canonical smoke baseline from `docs/04-delivery/local-dev.md` to confirm no regression.

## Exit criteria

- Duration data model is in place and documented.
- Seed path is idempotent and explicit for baseline services.
- No change in user-visible booking behavior before group-02.

## Group status

Status: DONE
Completed at: 2026-02-09
