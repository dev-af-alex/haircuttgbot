# API principles and contracts

## 1) API style

- REST/GraphQL/gRPC: REST (FastAPI HTTP endpoints).
- Versioning: internal baseline; public API versioning starts in later epics.
- Pagination: not applicable in current baseline.
- Idempotency: `GET /health` is idempotent and side-effect free.

## 2) Error model

- Error format: FastAPI default JSON error shape for now (to be standardized later).

## 3) AuthN/AuthZ

- Caller authentication: `GET /health` is intentionally unauthenticated for liveness checks.
- Permission checks: role resolution and RBAC decision endpoints support command authorization flow.

## 4) Implemented endpoints

- `GET /health`
  - Purpose: container and runtime health probe.
  - Response `200`: `{"status":"ok","service":"bot-api"}`

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
  - Purpose: return available 60-minute slots for selected master/date.
  - Request: `{"master_id":1,"date":"2026-02-09"}`
  - Response `200`:
    `{"slot_minutes":60,"slots":[{"start_at":"2026-02-09T10:00:00+00:00","end_at":"2026-02-09T11:00:00+00:00"}]}`
  - Behavior notes:
    - Excludes occupied active bookings, availability blocks, and lunch interval.
    - Excludes past slots for the current day.
    - Uses half-open interval overlap semantics (`[start, end)`).

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
  - Request: `{"master_id":1,"date":"2026-02-12"}`
  - Response `200`:
    `{"message":"Выберите доступный слот.","slots":[{"start_at":"2026-02-12T10:00:00+00:00","end_at":"2026-02-12T11:00:00+00:00"}]}`

- `POST /internal/telegram/client/booking-flow/confirm`
  - Purpose: confirm flow and create booking with notifications.
  - Request:
    `{"client_telegram_user_id":2000001,"master_id":1,"service_type":"haircut","slot_start":"2026-02-12T10:00:00+00:00"}`
  - Response `200` (success):
    `{"created":true,"booking_id":42,"message":"Запись успешно создана.","notifications":[{"recipient_telegram_user_id":2000001,"message":"Запись подтверждена."},{"recipient_telegram_user_id":1000001,"message":"Новая запись клиента добавлена в расписание."}]}`

- `POST /internal/telegram/client/booking-flow/cancel`
  - Purpose: cancel client-owned active future booking with participant notifications.
  - Request:
    `{"client_telegram_user_id":2000001,"booking_id":42}`
  - Response `200` (success):
    `{"cancelled":true,"booking_id":42,"message":"Запись успешно отменена.","notifications":[{"recipient_telegram_user_id":2000001,"message":"Ваша запись отменена."},{"recipient_telegram_user_id":1000001,"message":"Клиент отменил запись."}]}`
  - Response `200` (rejected example):
    `{"cancelled":false,"booking_id":null,"message":"Эту запись нельзя отменить.","notifications":[]}`

- `POST /internal/telegram/master/booking-flow/cancel`
  - Purpose: cancel master-owned active future booking with mandatory reason and participant notifications.
  - Request:
    `{"master_telegram_user_id":1000001,"booking_id":42,"reason":"Непредвиденные обстоятельства"}`
  - Response `200` (success):
    `{"cancelled":true,"booking_id":42,"message":"Запись успешно отменена.","notifications":[{"recipient_telegram_user_id":2000001,"message":"Мастер отменил запись. Причина: Непредвиденные обстоятельства"},{"recipient_telegram_user_id":1000001,"message":"Запись клиента отменена."}]}`
  - Response `200` (rejected example):
    `{"cancelled":false,"booking_id":null,"message":"Укажите причину отмены.","notifications":[]}`
  - Behavior notes:
    - Rejects cancellation if reason is empty/whitespace.
    - Rejects cancellation for bookings outside master ownership.

- Master schedule command contracts (baseline)
  - `day_off`: `{"master_telegram_user_id":1000001,"start_at":"2026-02-14T15:00:00+00:00","end_at":"2026-02-14T17:00:00+00:00","block_id":null}`
  - `lunch_update` (planned next group): `{"master_telegram_user_id":1000001,"lunch_start":"13:00","lunch_end":"14:00"}`
  - `manual_booking` (planned next groups): `{"master_telegram_user_id":1000001,"client_name":"Client Demo","service_type":"haircut","slot_start":"2026-02-14T12:00:00+00:00"}`
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
  - Behavior notes:
    - Rejects invalid interval (`start_at >= end_at`).
    - Rejects overlapping day-off intervals for the same master.
    - Updated day-off interval is immediately reflected in `POST /internal/availability/slots`.
