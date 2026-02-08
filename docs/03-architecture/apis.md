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
