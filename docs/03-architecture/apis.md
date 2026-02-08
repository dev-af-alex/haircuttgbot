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
