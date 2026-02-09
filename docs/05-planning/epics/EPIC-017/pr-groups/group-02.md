# EPIC-017 — PR Group 02

## Objective

Roll out master display-name rendering across client booking flow texts while preserving current business rules and callback idempotency.

## Scope

- Replace `Master ID` output with master display name in client master selection.
- Apply same display-name policy in booking confirmation outputs.
- Reuse one shared display-name helper from ADR-defined fallback order.
- Keep RBAC and booking validation behavior unchanged.

## Tasks included

- T-004 Integrate master display name into client master selection - DONE.
- T-005 Integrate master display name into booking confirmation texts - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable independently via merge commit.
- No destructive schema migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0, runtime services healthy).
- Existing smoke path stays green with updated text expectations.

## Acceptance checks

1. Client master selection outputs display name consistently.
2. Booking confirmation outputs display name consistently.
3. Display-name fallback behavior is deterministic when data is partial.
4. Existing booking create/cancel behavior remains unchanged.

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
