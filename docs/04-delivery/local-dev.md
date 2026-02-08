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
2. Wait until all services are healthy:
   `docker compose ps`
3. Run smoke test (below)
4. `docker compose down` to stop

## Ports

- `8080`: `bot-api` HTTP endpoint (`/health`)

## Services and health checks

- `postgres`: `pg_isready`
- `redis`: `redis-cli ping`
- `bot-api`: internal HTTP check against `http://127.0.0.1:8080/health`

## Smoke test (must pass on every PR)

1. Verify containers are up and healthy:
   `docker compose ps`
2. Check API health endpoint:
   `curl -fsS http://localhost:8080/health`
3. Expected response contains:
   `{"status":"ok","service":"bot-api"}`
4. Confirm startup structured log exists:
   `docker compose logs bot-api --tail=50 | grep '"event": "startup"'`

## Notes

- Current baseline includes runtime skeleton only; booking business flows are added in next epics.
- Do not commit secrets or real bot tokens.
