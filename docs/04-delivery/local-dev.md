# Local development via docker-compose (SSOT)

## Definition: "system runs locally"

A developer can run:

- `docker compose up -d`
- a smoke test
  and get a successful result.

## Prerequisites

- Docker Engine
- Docker Compose v2 (`docker compose`)
- Optional: copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN` for real Telegram integration tests

## Local run steps (must be kept current)

1. `docker compose up -d --build`
2. Verify migration completed successfully:
   `docker compose ps -a`
3. Seed baseline data (2 masters):
   `docker compose exec -T bot-api python -m app.db.seed`
4. Wait until `bot-api`, `postgres`, and `redis` are healthy:
   `docker compose ps`
5. Run smoke test (below)
6. `docker compose down` to stop

## Ports

- `8080`: `bot-api` HTTP endpoint (`/health`)

## Services and health checks

- `postgres`: `pg_isready`
- `redis`: `redis-cli ping`
- `migrate`: one-shot Alembic migration service (`alembic upgrade head`)
- `bot-api`: internal HTTP check against `http://127.0.0.1:8080/health`

## Smoke test (must pass on every PR)

1. Verify migration service completed:
   `docker compose ps -a`
2. Seed baseline records:
   `docker compose exec -T bot-api python -m app.db.seed`
3. Check API health endpoint:
   `curl -fsS http://localhost:8080/health`
4. Validate seed result (at least 2 masters):
   `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT count(*) FROM masters;"`
5. Confirm startup structured log exists:
   `docker compose logs bot-api --tail=50 | grep '"event": "startup"'`

## Notes

- Runtime skeleton includes automatic migration execution via `migrate` service.
- Do not commit secrets or real bot tokens.
