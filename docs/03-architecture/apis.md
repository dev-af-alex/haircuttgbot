# API principles and contracts

## 1) API style

- REST/GraphQL/gRPC: REST (FastAPI HTTP endpoints).
- Versioning: internal baseline; public API versioning starts in later epics.
- Pagination: not applicable in current baseline.
- Idempotency:
  - `GET /health` is idempotent and side-effect free.
  - Telegram write-side commands use bounded replay-idempotency guard (see endpoint notes).

## 2) Error model

- Error format: FastAPI default JSON error shape for now (to be standardized later).

## 3) AuthN/AuthZ

- Caller authentication: `GET /health` is intentionally unauthenticated for liveness checks.
- Permission checks: role resolution and RBAC decision endpoints support command authorization flow.

Runtime ingress note:

- Real Telegram updates ingress uses aiogram polling mode in current baseline (`TELEGRAM_UPDATES_MODE=polling`).
- Webhook ingress mode is not enabled in this baseline.
- Telegram chat command handlers are registered in aiogram dispatcher and map to existing booking/schedule services.
- Background reminder worker runs in-process and dispatches due booking reminders to Telegram when token is configured.

Telegram command contract baseline:

- Shared:
  - `/start`, `/help`: show role-aware help and supported commands.
- Client commands:
  - `/client_start`
  - `/client_master <master_id>`
  - `/client_slots <master_id> <YYYY-MM-DD>`
  - `/client_book <master_id> <service_type> <YYYY-MM-DDTHH:MM:SS+00:00>`
  - `/client_cancel <booking_id>`
- Master commands:
  - `/master_cancel <booking_id> <reason>`
  - `/master_dayoff <YYYY-MM-DDTHH:MM:SS+00:00> <YYYY-MM-DDTHH:MM:SS+00:00> [block_id]`
  - `/master_lunch <HH:MM:SS> <HH:MM:SS>`
  - `/master_manual <service_type> <YYYY-MM-DDTHH:MM:SS+00:00> <client_text>`

## 4) Implemented endpoints

- `GET /health`
  - Purpose: container and runtime health probe.
  - Response `200`: `{"status":"ok","service":"bot-api"}`

- `GET /metrics`
  - Purpose: Prometheus metrics endpoint for runtime health and booking/API telemetry.
  - Response `200`: text/plain in Prometheus exposition format.
  - Includes:
    - `bot_api_service_health` gauge (`1` healthy, `0` unhealthy).
    - `bot_api_requests_total{method,path,status_code}` counter.
    - `bot_api_request_latency_seconds{method,path}` histogram.
    - `bot_api_booking_outcomes_total{action,outcome}` counter.
    - `bot_api_master_admin_outcomes_total{action,outcome}` counter.
    - `bot_api_abuse_outcomes_total{path,outcome}` counter (`allow`/`deny` for Telegram throttling checks).
    - `bot_api_telegram_delivery_outcomes_total{path,outcome}` counter
      (`processed_success`, `processed_rejected`, `replayed`, `throttled`, `failed_transient`, `failed_terminal`).

- `POST /internal/auth/resolve-role`
  - Purpose: resolve role by `telegram_user_id` from DB mapping.
  - Request: `{"telegram_user_id": 1000001}`
  - Response: `{"role":"Master"}` or `{"role":null}`

- `POST /internal/commands/authorize`
  - Purpose: evaluate RBAC decision for command + user.
  - Request: `{"telegram_user_id":1000001,"command":"master:schedule"}`
  - Response: `{"allowed":true,"role":"Master","message":"Команда разрешена."}`

- `GET /internal/booking/service-options`
  - Purpose: return canonical client booking service options and Russian labels.
  - Response `200`:
    `{"service_options":[{"code":"haircut","label":"Стрижка"},{"code":"beard","label":"Борода"},{"code":"haircut_beard","label":"Стрижка + борода"}]}`

- `POST /internal/availability/slots`
  - Purpose: return available slots for selected master/date, with optional service-duration awareness.
  - Request (legacy-compatible): `{"master_id":1,"date":"2026-02-09"}`
  - Request (service-aware): `{"master_id":1,"date":"2026-02-09","service_type":"haircut"}`
  - Response `200`:
    `{"slot_minutes":30,"slots":[{"start_at":"2026-02-09T10:00:00+00:00","end_at":"2026-02-09T10:30:00+00:00"}]}`
  - Behavior notes:
    - Excludes occupied active bookings, availability blocks, and lunch interval.
    - Excludes past slots for the current day.
    - Uses half-open interval overlap semantics (`[start, end)`).
    - If `service_type` is omitted, endpoint keeps 60-minute baseline slot generation for backward compatibility.

- `POST /internal/booking/create`
  - Purpose: create a client booking for selected master/service/slot.
  - Request:
    `{"master_id":1,"client_user_id":2000001,"service_type":"haircut","slot_start":"2026-02-11T10:00:00+00:00"}`
  - Response `200` (success):
    `{"created":true,"booking_id":42,"message":"Запись успешно создана."}`
  - Response `200` (validation reject example):
    `{"created":false,"booking_id":null,"message":"У клиента уже есть активная будущая запись."}`
  - Behavior notes:
    - Validates service option code against canonical contract.
    - Rejects overlap with active booking/day-off/manual blocks/lunch and out-of-work-window slots.
    - Enforces at most one active future booking per client.

- Booking cancellation contract (domain baseline)
  - Canonical statuses: `active`, `cancelled_by_client`, `cancelled_by_master`, `completed`.
  - Allowed transitions:
    - `active -> cancelled_by_client`
    - `active -> cancelled_by_master`
    - `active -> completed`
  - Cancellation reason policy:
    - `cancelled_by_client`: reason is optional (not required).
    - `cancelled_by_master`: reason is required.

- `GET /internal/telegram/client/booking-flow/start`
  - Purpose: start client booking flow (master selection step).
  - Response `200`:
    `{"message":"Выберите мастера.","masters":[{"id":1,"display_name":"Master Demo 1","telegram_user_id":1000001}]}`

- `POST /internal/telegram/client/booking-flow/select-master`
  - Purpose: move flow to service selection after master choice.
  - Request: `{"master_id":1}`
  - Response `200`:
    `{"message":"Выберите услугу.","service_options":[{"code":"haircut","label":"Стрижка"}]}`

- `POST /internal/telegram/client/booking-flow/select-service`
  - Purpose: move flow to slot selection after service/date choice.
  - Request (current baseline): `{"master_id":1,"date":"2026-02-12"}`
  - Request (service-aware): `{"master_id":1,"date":"2026-02-12","service_type":"haircut"}`
  - Response `200`:
    `{"message":"Выберите доступный слот.","slots":[{"start_at":"2026-02-12T10:00:00+00:00","end_at":"2026-02-12T11:00:00+00:00"}]}`

- `POST /internal/telegram/client/booking-flow/confirm`
  - Purpose: confirm flow and create booking with notifications.
  - Request:
    `{"client_telegram_user_id":2000001,"master_id":1,"service_type":"haircut","slot_start":"2026-02-12T10:00:00+00:00"}`
  - Response `200` (success):
    `{"created":true,"booking_id":42,"message":"Запись успешно создана.","notifications":[{"recipient_telegram_user_id":2000001,"message":"Запись подтверждена."},{"recipient_telegram_user_id":1000001,"message":"Новая запись клиента добавлена в расписание.\nКлиент: @client_a\nТелефон: +79991234567\nСлот: 12.02.2026 13:00\nУслуга: Стрижка"}]}`
  - Idempotency notes:
    - Duplicate delivery in replay window returns cached success payload.
    - Replay response includes header `X-Idempotency-Replayed: 1`.

- `POST /internal/telegram/client/booking-flow/cancel`
  - Purpose: cancel client-owned active future booking with participant notifications.
  - Request:
    `{"client_telegram_user_id":2000001,"booking_id":42}`
  - Response `200` (success):
    `{"cancelled":true,"booking_id":42,"message":"Запись успешно отменена.","notifications":[{"recipient_telegram_user_id":2000001,"message":"Ваша запись отменена."},{"recipient_telegram_user_id":1000001,"message":"Клиент отменил запись."}]}`
  - Response `200` (rejected example):
    `{"cancelled":false,"booking_id":null,"message":"Эту запись нельзя отменить.","notifications":[]}`
  - Response `429` (abuse throttled):
    `{"detail":"Слишком много запросов. Повторите позже.","code":"throttled","retry_after_seconds":5}`
  - Idempotency notes:
    - Successful cancellation responses are replayed for duplicate deliveries in replay window.
    - Replay response includes header `X-Idempotency-Replayed: 1`.
  - Grouped-booking note (EPIC-026):
    - For grouped participant bookings, cancellation ownership additionally allows organizer ownership path (`organizer_user_id`) and remains participant-level (one booking per cancel action).

- `POST /internal/telegram/master/booking-flow/cancel`
  - Purpose: cancel master-owned active future booking with mandatory reason and participant notifications.
  - Request:
    `{"master_telegram_user_id":1000001,"booking_id":42,"reason":"Непредвиденные обстоятельства"}`
  - Response `200` (success):
    `{"cancelled":true,"booking_id":42,"message":"Запись успешно отменена.","notifications":[{"recipient_telegram_user_id":2000001,"message":"Мастер отменил запись. Причина: Непредвиденные обстоятельства\nСлот: 13.02.2026 13:00"},{"recipient_telegram_user_id":1000001,"message":"Запись клиента отменена."}]}`
  - Response `200` (rejected example):
    `{"cancelled":false,"booking_id":null,"message":"Укажите причину отмены.","notifications":[]}`
  - Response `429` (abuse throttled):
    `{"detail":"Слишком много запросов. Повторите позже.","code":"throttled","retry_after_seconds":5}`
  - Idempotency notes:
    - Successful cancellation responses are replayed for duplicate deliveries in replay window.
    - Replay response includes header `X-Idempotency-Replayed: 1`.
  - Behavior notes:
    - Rejects cancellation if reason is empty/whitespace.
    - Rejects cancellation for bookings outside master ownership.

- Master schedule command contracts (baseline)
  - `day_off`: `{"master_telegram_user_id":1000001,"start_at":"2026-02-14T15:00:00+00:00","end_at":"2026-02-14T17:00:00+00:00","block_id":null}`
  - `lunch_update`: `{"master_telegram_user_id":1000001,"lunch_start":"15:00:00","lunch_end":"16:00:00"}`
  - `manual_booking`: `{"master_telegram_user_id":1000001,"client_name":"Новый клиент (walk-in)","service_type":"haircut","slot_start":"2026-02-14T12:00:00+00:00"}`
  - Ownership resolution: every master schedule command resolves `master_telegram_user_id -> users.id -> masters.id` and applies changes only to that master profile.

- `POST /internal/telegram/master/schedule/day-off`
  - Purpose: create/update master day-off interval as availability block for own profile.
  - Request:
    `{"master_telegram_user_id":1000001,"start_at":"2026-02-14T15:00:00+00:00","end_at":"2026-02-14T17:00:00+00:00","block_id":null}`
  - Response `200` (create success):
    `{"applied":true,"created":true,"block_id":101,"message":"Выходной интервал сохранен."}`
  - Response `200` (update success):
    `{"applied":true,"created":false,"block_id":101,"message":"Выходной интервал обновлен."}`
  - Response `200` (rejected example):
    `{"applied":false,"created":false,"block_id":null,"message":"Выходной интервал пересекается с существующим выходным."}`
  - Response `429` (abuse throttled):
    `{"detail":"Слишком много запросов. Повторите позже.","code":"throttled","retry_after_seconds":5}`
  - Idempotency notes:
    - Successful `applied=true` responses are replayed for duplicate deliveries in replay window.
    - Replay response includes header `X-Idempotency-Replayed: 1`.
  - Behavior notes:
    - Rejects invalid interval (`start_at >= end_at`).
    - Rejects overlapping day-off intervals for the same master.
    - Day-off overlap checks use shared half-open interval predicate.
    - Updated day-off interval is immediately reflected in `POST /internal/availability/slots`.

- `POST /internal/telegram/master/schedule/lunch`
  - Purpose: update master lunch-break window for own profile.
  - Request:
    `{"master_telegram_user_id":1000001,"lunch_start":"15:00:00","lunch_end":"16:00:00"}`
  - Response `200` (success):
    `{"applied":true,"message":"Обеденный перерыв обновлен."}`
  - Response `200` (rejected example):
    `{"applied":false,"message":"Длительность обеда должна быть 60 минут."}`
  - Response `429` (abuse throttled):
    `{"detail":"Слишком много запросов. Повторите позже.","code":"throttled","retry_after_seconds":5}`
  - Idempotency notes:
    - Successful `applied=true` responses are replayed for duplicate deliveries in replay window.
    - Replay response includes header `X-Idempotency-Replayed: 1`.
  - Behavior notes:
    - Rejects invalid interval (`lunch_start >= lunch_end`).
    - Rejects non-60-minute duration and intervals outside master work window.
    - Updated lunch interval is enforced by `POST /internal/availability/slots` and `POST /internal/booking/create`.

- `POST /internal/telegram/master/schedule/manual-booking`
  - Purpose: create master-owned manual booking for offline request.
  - Request:
    `{"master_telegram_user_id":1000001,"client_name":"Client Demo","service_type":"haircut","slot_start":"2026-02-16T12:00:00+00:00"}`
  - Response `200` (success):
    `{"applied":true,"booking_id":200,"message":"Ручная запись создана."}`
  - Response `200` (rejected example):
    `{"applied":false,"booking_id":null,"message":"Слот для ручной записи недоступен."}`
  - Response `429` (abuse throttled):
    `{"detail":"Слишком много запросов. Повторите позже.","code":"throttled","retry_after_seconds":5}`
  - Idempotency notes:
    - Successful `applied=true` responses are replayed for duplicate deliveries in replay window.
    - Replay response includes header `X-Idempotency-Replayed: 1`.
  - Behavior notes:
    - Applies ownership check to target master profile.
    - `client_name` accepts arbitrary non-empty text (up to 160 chars) and is persisted in booking context.
    - Rejects overlap with active bookings, day-off blocks, and lunch interval using shared half-open interval predicate.
    - Created manual booking occupies slot for subsequent availability and booking checks.

## 5) Telegram delivery retry/error policy baseline (EPIC-010 group-02)

- Scope: Telegram write-side endpoints guarded by idempotency middleware.
- Outcome classes:
  - `processed_success`: successful write-side effect (`created/cancelled/applied == true`); terminal, no retry.
  - `processed_rejected`: business-rule rejection (`created/cancelled/applied == false`); terminal, no retry.
  - `replayed`: duplicate delivery answered from idempotency cache; terminal, no retry.
  - `throttled`: abuse-throttle deny (`429`); retriable after `retry_after_seconds`.
  - `failed_transient`: server-side/transient failure (`5xx` or middleware-caught exception); retriable.
  - `failed_terminal`: non-retriable response outside the classes above.
- Observability mapping:
  - Metric: `bot_api_telegram_delivery_outcomes_total{path,outcome}`.
  - Event: `telegram_delivery_outcome` with fields
    `telegram_user_id`, `path`, `method`, `status_code`, `outcome`, `retry_recommended`.
  - Replay-specific event remains: `telegram_idempotency_replay`.

## 6) Observability event schema

- Structured log baseline:
  - Every event is a JSON object with at least: `event`, `service`, `ts`.
  - `service` is fixed as `bot-api`.
  - `ts` uses ISO-8601 UTC timestamp.
- Event names currently emitted:
  - `startup`
  - `rbac_deny`
  - `booking_create`
  - `booking_flow_confirm`
  - `booking_flow_cancel_client`
  - `booking_flow_cancel_master`
  - `schedule_day_off_upsert`
  - `schedule_lunch_update`
  - `schedule_manual_booking`
  - `master_admin_action`
  - `abuse_throttle_deny`
  - `telegram_idempotency_replay`
  - `telegram_delivery_outcome`
  - `telegram_delivery_error`
  - `telegram_updates_runtime_started`
  - `telegram_updates_runtime_disabled`
  - `booking_reminder_schedule`
  - `booking_reminder_worker_started`
  - `booking_reminder_worker_disabled`
  - `booking_reminder_dispatch`
  - `booking_reminder_dispatch_error`
- Redaction policy:
  - Keys containing `token`, `secret`, `password`, `authorization`, `api_key`, `database_url`, `phone` are replaced with `[REDACTED]`.
  - Raw `TELEGRAM_BOT_TOKEN` value is masked from any string field if present.

Booking reminder delivery policy (EPIC-023 baseline):

- Reminder path key for observability: `/internal/telegram/client/booking-reminder`.
- Scheduling outcomes:
  - `scheduled`: booking qualifies for 2-hour reminder.
  - `skipped`: booking created less than 2 hours before slot start.
  - `replayed`: scheduling request is duplicate for same booking.
  - `failed`: schedule persistence/validation failed.
- Dispatch outcomes:
  - `sent`: reminder message delivered to Telegram recipient.
  - `failed`: dispatch/send attempt failed (kept pending for next poll retry).
