# EPIC-013 / PR Group 01

## Objective

Deliver a mergeable bootstrap identity foundation that guarantees required RBAC baseline records and a configured bootstrap master without breaking existing local runtime.

## Scope

- Finalize and record bootstrap provisioning strategy (ADR + env contract).
- Implement idempotent role/bootstrap-master provisioning in startup path.
- Add fail-fast validation for missing/invalid bootstrap Telegram ID.
- Add baseline automated tests for idempotency and startup validation behavior.

## Included tasks

- T-001 - DONE
- T-002 - DONE

## Mergeability and runtime safety

- Keep `docker compose up -d` as canonical startup path.
- Preserve existing seed/smoke behavior for current booking/cancellation/schedule flows.
- Use backward-compatible DB updates only (no destructive migration in this group).

## Acceptance checks

1. Clean startup creates required roles and configured bootstrap master exactly once.
2. Re-running bootstrap path does not create duplicates and keeps existing mappings valid.
3. Missing/invalid bootstrap Telegram ID stops startup with deterministic operator-facing error.
4. Existing smoke checks continue to pass after merge.

## Validation commands

```bash
docker compose up -d --build
docker compose ps -a
.venv/bin/pytest -q
curl -fsS http://127.0.0.1:8080/health
docker compose exec -T bot-api python -m app.db.seed
```

## Group status

Status: DONE
Completed at: 2026-02-09

## Risks and mitigations

- Risk: bootstrap provisioning path conflicts with existing seed logic.
  - Mitigation: define a single source of bootstrap truth in ADR and enforce idempotent UPSERT semantics.
- Risk: operator misconfiguration blocks runtime unexpectedly.
  - Mitigation: fail fast with explicit config error message and documented recovery steps.
