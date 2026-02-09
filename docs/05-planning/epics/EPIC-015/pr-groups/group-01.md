# EPIC-015 — PR Group 01

## Objective

Deliver a mergeable foundation for readable-time localization and mobile keyboard layout constraints without changing core booking/schedule business rules.

## Scope

- Finalize formatting/layout decision in ADR for EPIC-015.
- Add shared readable-time formatter utility for user-visible slot/date output.
- Add reusable keyboard row-width/layout helper for phone-friendly button composition.
- Keep existing callback routing, RBAC checks, and idempotent write behavior unchanged.

## Tasks included

- T-001 Finalize readable time + mobile keyboard contract - DONE.
- T-002 Implement shared readable-time formatter utility - DONE.
- T-003 Add keyboard row-layout helper constraints - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable by merge commit independently.
- No destructive schema/data migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0; `bot-api`, `postgres`, `redis` healthy).
- Existing end-to-end booking/schedule smoke path remains functional after merge.

## Acceptance checks

1. ADR stub is updated with clear formatter and keyboard constraints decision inputs for implementation groups.
2. Shared formatter renders deterministic `ru` date/time strings for representative 30-minute and 60-minute slot cases.
3. Keyboard layout helper enforces row-width constraints without changing callback payload semantics.
4. Canonical smoke baseline from `docs/04-delivery/local-dev.md` passes with no flow regression.

## Validation commands

```bash
docker compose up -d --build
docker compose ps -a
.venv/bin/pytest -q
curl -fsS http://127.0.0.1:8080/health
```

## Group status

Status: DONE
Completed at: 2026-02-09
