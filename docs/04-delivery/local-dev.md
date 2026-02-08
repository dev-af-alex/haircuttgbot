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
6. Validate booking flow success + one-active-future-booking rejection:
   `docker compose exec -T bot-api python - <<'PY'
import json
import urllib.request
from sqlalchemy import create_engine, text
from app.db.session import get_database_url

client_tg = 2001001
slot_1 = "2026-02-13T10:00:00+00:00"
slot_2 = "2026-02-13T12:00:00+00:00"

engine = create_engine(get_database_url(), future=True)
with engine.begin() as conn:
    conn.execute(text("INSERT INTO roles (name) VALUES ('Client') ON CONFLICT (name) DO NOTHING"))
    conn.execute(
        text(
            "INSERT INTO users (telegram_user_id, role_id) VALUES (:telegram_user_id, (SELECT id FROM roles WHERE name='Client')) ON CONFLICT (telegram_user_id) DO NOTHING"
        ),
        {"telegram_user_id": client_tg},
    )
    conn.execute(
        text(
            "DELETE FROM bookings WHERE client_user_id = (SELECT id FROM users WHERE telegram_user_id = :telegram_user_id)"
        ),
        {"telegram_user_id": client_tg},
    )

payload = {
    "client_telegram_user_id": client_tg,
    "master_id": 1,
    "service_type": "haircut",
    "slot_start": slot_1,
}
req = urllib.request.Request(
    "http://127.0.0.1:8080/internal/telegram/client/booking-flow/confirm",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
first = json.loads(urllib.request.urlopen(req).read().decode())
payload["slot_start"] = slot_2
second_req = urllib.request.Request(
    "http://127.0.0.1:8080/internal/telegram/client/booking-flow/confirm",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
second = json.loads(urllib.request.urlopen(second_req).read().decode())
assert first["created"] is True
assert second["created"] is False
print({"first": first, "second": second})
PY`

## Notes

- Runtime skeleton includes automatic migration execution via `migrate` service.
- Do not commit secrets or real bot tokens.
