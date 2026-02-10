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
- Optional: copy `.env.example` to `.env`, set `TELEGRAM_BOT_TOKEN`, and keep `TELEGRAM_UPDATES_MODE=polling` for real Telegram integration tests.
- Required bootstrap config: `BOOTSTRAP_MASTER_TELEGRAM_ID` must be a positive integer Telegram user ID (compose default is `1000001`).
- Business time config: `BUSINESS_TIMEZONE` must be a valid IANA timezone (compose default is `Europe/Moscow`).

## Local run steps (must be kept current)

1. `docker compose up -d --build`
2. Verify migration completed successfully:
   `docker compose ps -a`
3. Seed baseline data (bootstrap owner only):
   `docker compose exec -T bot-api python -m app.db.seed`
4. Wait until `bot-api`, `postgres`, and `redis` are healthy:
   `docker compose ps`
5. Run smoke test (below)
6. (Recommended) Run unit tests from project virtualenv:
   `.venv/bin/pytest -q`
7. (Optional) Verify Telegram polling runtime state in startup logs:
   `docker compose logs bot-api --tail=200 | grep 'telegram_updates_runtime'`
8. `docker compose down` to stop

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
   `curl -fsS http://127.0.0.1:8080/metrics | grep -E 'bot_api_service_health|bot_api_requests_total|bot_api_request_latency_seconds|bot_api_booking_outcomes_total|bot_api_master_admin_outcomes_total|bot_api_abuse_outcomes_total|bot_api_telegram_delivery_outcomes_total'`
5. Validate clean first-deploy seed baseline (only bootstrap owner user/master before first organic `/start`):
   `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT count(*) FROM users;"`
   `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT count(*) FROM masters;"`
6. Validate seeded service catalog durations:
   `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT code, duration_minutes FROM services ORDER BY code;"`
7. Confirm startup structured log exists:
   `docker compose logs bot-api --tail=200 | grep '"event": "startup"'`
   `docker compose logs bot-api --tail=200 | grep '"business_timezone": "Europe/Moscow"'`
8. Validate functional smoke coverage via automated test suite (no inline scripts in docs):
   `.venv/bin/pytest -q tests/test_health.py tests/test_idempotency.py tests/test_booking.py tests/test_telegram_callbacks.py tests/test_telegram_master_callbacks.py tests/test_master_admin.py tests/test_throttling.py tests/test_observability.py tests/test_timezone.py`
   - Coverage must include mixed-duration booking behavior (30-minute and 60-minute service scenarios) via `tests/test_booking.py` and callback flow tests.
9. Rehearse PostgreSQL backup/restore once per release candidate (or when schema changes):
   follow `docs/04-delivery/postgresql-backup-restore.md`

## Optional real Telegram validation (polling mode)

Use this sequence when validating aiogram runtime against a real Telegram chat.

1. Configure `.env`:
   - `TELEGRAM_BOT_TOKEN=<your_bot_token>`
   - `TELEGRAM_UPDATES_MODE=polling`
   - `BUSINESS_TIMEZONE=Europe/Moscow`
2. Start stack and seed baseline:
   - `docker compose up -d --build`
   - `docker compose exec -T bot-api python -m app.db.seed`
3. Ensure polling runtime is active:
   - `docker compose logs bot-api --tail=200 | grep 'telegram_updates_runtime_started'`
   - `docker compose logs bot-api --tail=200 | grep 'business_timezone'`
4. In Telegram chat with bot run `/start` from a Telegram account that is not pre-seeded in DB:
   - verify greeting + direct role landing to `Меню клиента`;
   - optional DB check (replace `YOUR_TG_ID`): `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT telegram_user_id, telegram_username FROM users WHERE telegram_user_id=YOUR_TG_ID;"`
5. Validate button-first client flow:
   - tap `Новая запись`;
   - choose master -> service -> date -> slot -> confirm;
   - then tap `Отменить запись` and confirm cancel for created booking.
6. Validate key rejection path in chat:
   - create one future booking;
   - start a second booking attempt through buttons and confirm bot returns one-active-booking rejection.
7. Validate mixed-duration slot behavior in chat:
   - in `Новая запись`, choose `Стрижка` and confirm 30-minute slot range labels are present (for example `10:00-10:30`, `10:30-11:00`);
   - restart booking flow, choose `Стрижка + борода` and confirm hourly slot range labels (for example `10:00-11:00`, and no `10:30-11:30` starts).
8. Optional master-role validation can be run with bootstrap master account (`BOOTSTRAP_MASTER_TELEGRAM_ID`):
   - run `/start`, verify greeting + direct role landing to `Меню мастера`, and validate buttons:
     - `Просмотр расписания`
     - `Выходной день`
     - `Обед`
     - `Ручная запись`
     - `Отмена записи` (reason selection is mandatory).
   - verify readable master texts:
     - `Просмотр расписания` output uses `DD.MM.YYYY HH:MM` slot labels and `HH:MM-HH:MM` lunch interval;
     - `Просмотр расписания` first asks for target date, then returns schedule for selected date;
     - `Выходной день` and `Обед` confirmations include readable interval/date details;
     - `Ручная запись` asks for free-text client value (любой текст), and confirmation/result include `Клиент` + readable `Слот` details;
     - `Отмена записи` confirmations include readable `Слот` details and reason context.
   - verify informative notifications:
     - on client booking creation master notification includes client context (`@nickname`, and phone when present) plus exact slot date/time;
     - on master cancellation client notification includes reason and exact cancelled slot date/time.
   - validate EPIC-016 guardrails:
     - if current time in `BUSINESS_TIMEZONE` is `15:00`, in client `Новая запись` same-day slots earlier than `15:30` are not offered;
     - for an occupied date, `Выходной день` returns rejection text about existing active bookings.
9. Optional bootstrap-master administration validation (same master account as `BOOTSTRAP_MASTER_TELEGRAM_ID`):
   - in `Мастер` menu open `Управление мастерами`;
   - ensure target client opened bot with `/start` at least once;
   - verify target nickname captured in DB (replace `TARGET_TG_ID`):
     - `docker compose exec -T postgres psql -U haircuttgbot -d haircuttgbot -c "SELECT telegram_username FROM users WHERE telegram_user_id=TARGET_TG_ID;"`
   - run `Добавить мастера`, send message `@<captured_nickname>`, and check success message;
   - retry with invalid value (`candidate_master`) and check deterministic format rejection;
   - retry with unknown nickname (`@unknown_user`) and check deterministic not-found rejection;
   - run `Переименовать мастера`, select the same target, submit new display name (for example `Master Renamed`), and verify success message;
   - retry rename with invalid value (` `) and check deterministic validation rejection;
   - run `Удалить мастера` for the same user and check success message;
   - from non-bootstrap master account confirm deny response for admin actions.
10. Stop stack:
   - `docker compose down`

## Notes

- Runtime skeleton includes automatic migration execution via `migrate` service.
- Telegram updates runtime mode is controlled by `TELEGRAM_UPDATES_MODE` (`polling` by default, `disabled` to skip aiogram polling startup).
- Do not embed multi-line smoke scripts (heredoc/inline Python) in this document; keep smoke validation as explicit commands and automated tests.
- Run host-side Python tooling via virtualenv binaries (for example: `.venv/bin/pytest`, `.venv/bin/bandit`).
- Do not commit secrets or real bot tokens.
- Backup rehearsal commands and retention baseline are documented in `docs/04-delivery/postgresql-backup-restore.md`.
- Alert thresholds and incident response notes are documented in `docs/04-delivery/alerts-baseline.md`.
