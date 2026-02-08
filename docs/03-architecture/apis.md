# API principles and contracts

## 1) API style

- REST/GraphQL/gRPC: REST (FastAPI HTTP endpoints).
- Versioning: internal baseline for EPIC-001; public API versioning starts in later epics.
- Pagination: not applicable in EPIC-001 baseline.
- Idempotency: `GET /health` is idempotent and side-effect free.

## 2) Error model

- Error format: FastAPI default JSON error shape for now (to be standardized in later epics).

## 3) AuthN/AuthZ

- Caller authentication: `GET /health` is intentionally unauthenticated for liveness checks.
- Permission checks: not applicable for current health endpoint; role-based checks start with Telegram command handlers.

## 4) Implemented endpoints (EPIC-001 baseline)

- `GET /health`
  - Purpose: container and runtime health probe.
  - Response `200`: `{"status":"ok","service":"bot-api"}`
