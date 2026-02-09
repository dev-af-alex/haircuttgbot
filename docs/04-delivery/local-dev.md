# Local development via docker-compose (SSOT)

## Definition: "system runs locally"

A developer can run:

- `docker compose up -d`
- a smoke test
  and get a successful result.

## Prerequisites

- Docker Engine
- Docker Compose v2 (`docker compose`)
- Optional for host-side unit tests: Python 3.12 virtualenv with dependencies installed in `.venv`
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
6. (Recommended) Run unit tests from project virtualenv:
   `.venv/bin/pytest -q`
7. `docker compose down` to stop

## Ports

- `8080`: `bot-api` HTTP endpoint (`/health`)
  - observability endpoint: `/metrics`

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
   `curl -fsS http://127.0.0.1:8080/health`
4. Check metrics endpoint and core metric families:
   `curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_service_health|bot_api_requests_total|bot_api_request_latency_seconds|bot_api_booking_outcomes_total'`
5. Validate seed result (at least 2 masters):
   `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT count(*) FROM masters;"`
6. Confirm startup structured log exists:
   `docker compose logs bot-api --tail=50 | grep '"event": "startup"'`
7. Validate booking/cancellation flow + master schedule updates (day-off/lunch/manual booking):
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
    conn.execute(
        text(
            """
            DELETE FROM bookings
            WHERE master_id = 1
              AND slot_start >= '2026-02-16T00:00:00+00:00'
              AND slot_start < '2026-02-17T00:00:00+00:00'
            """
        )
    )
    conn.execute(
        text(
            """
            DELETE FROM availability_blocks
            WHERE master_id = 1
              AND start_at >= '2026-02-16T00:00:00+00:00'
              AND start_at < '2026-02-17T00:00:00+00:00'
            """
        )
    )
    conn.execute(
        text(
            """
            UPDATE masters
            SET lunch_start = '13:00:00',
                lunch_end = '14:00:00'
            WHERE id = 1
            """
        )
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

cancel_req = urllib.request.Request(
    "http://127.0.0.1:8080/internal/telegram/client/booking-flow/cancel",
    data=json.dumps(
        {
            "client_telegram_user_id": client_tg,
            "booking_id": first["booking_id"],
        }
    ).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
cancelled = json.loads(urllib.request.urlopen(cancel_req).read().decode())
assert cancelled["cancelled"] is True

third_req = urllib.request.Request(
    "http://127.0.0.1:8080/internal/telegram/client/booking-flow/confirm",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
third = json.loads(urllib.request.urlopen(third_req).read().decode())
assert third["created"] is True

master_cancel_without_reason = urllib.request.Request(
    "http://127.0.0.1:8080/internal/telegram/master/booking-flow/cancel",
    data=json.dumps(
        {
            "master_telegram_user_id": 1000001,
            "booking_id": third["booking_id"],
            "reason": " ",
        }
    ).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
master_cancel_result = json.loads(urllib.request.urlopen(master_cancel_without_reason).read().decode())
assert master_cancel_result["cancelled"] is False
assert "причину" in master_cancel_result["message"].lower()

# EPIC-006 checks: day-off / lunch update / manual booking
day_off_req = urllib.request.Request(
    "http://127.0.0.1:8080/internal/telegram/master/schedule/day-off",
    data=json.dumps(
        {
            "master_telegram_user_id": 1000001,
            "start_at": "2026-02-16T15:00:00+00:00",
            "end_at": "2026-02-16T16:00:00+00:00",
        }
    ).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
day_off_result = json.loads(urllib.request.urlopen(day_off_req).read().decode())
assert day_off_result["applied"] is True

lunch_req = urllib.request.Request(
    "http://127.0.0.1:8080/internal/telegram/master/schedule/lunch",
    data=json.dumps(
        {
            "master_telegram_user_id": 1000001,
            "lunch_start": "18:00:00",
            "lunch_end": "19:00:00",
        }
    ).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
lunch_result = json.loads(urllib.request.urlopen(lunch_req).read().decode())
assert lunch_result["applied"] is True

manual_req = urllib.request.Request(
    "http://127.0.0.1:8080/internal/telegram/master/schedule/manual-booking",
    data=json.dumps(
        {
            "master_telegram_user_id": 1000001,
            "client_name": "Offline Smoke Client",
            "service_type": "haircut",
            "slot_start": "2026-02-16T12:00:00+00:00",
        }
    ).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
manual_result = json.loads(urllib.request.urlopen(manual_req).read().decode())
assert manual_result["applied"] is True

manual_overlap_req = urllib.request.Request(
    "http://127.0.0.1:8080/internal/telegram/master/schedule/manual-booking",
    data=json.dumps(
        {
            "master_telegram_user_id": 1000001,
            "client_name": "Offline Smoke Client 2",
            "service_type": "beard",
            "slot_start": "2026-02-16T12:30:00+00:00",
        }
    ).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
manual_overlap_result = json.loads(urllib.request.urlopen(manual_overlap_req).read().decode())
assert manual_overlap_result["applied"] is False

print(
    {
        "first": first,
        "second": second,
        "cancelled": cancelled,
        "third": third,
        "master_cancel_result": master_cancel_result,
        "day_off_result": day_off_result,
        "lunch_result": lunch_result,
        "manual_result": manual_result,
        "manual_overlap_result": manual_overlap_result,
    }
)
PY`
8. Rehearse PostgreSQL backup/restore once per release candidate (or when schema changes):
   follow `docs/04-delivery/postgresql-backup-restore.md`

## Notes

- Runtime skeleton includes automatic migration execution via `migrate` service.
- Run host-side Python tooling via virtualenv binaries (for example: `.venv/bin/pytest`, `.venv/bin/bandit`).
- Do not commit secrets or real bot tokens.
- Backup rehearsal commands and retention baseline are documented in `docs/04-delivery/postgresql-backup-restore.md`.
- Alert thresholds and incident response notes are documented in `docs/04-delivery/alerts-baseline.md`.
