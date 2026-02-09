# EPIC-012 / PR Group 01

## Objective

Create a mergeable foundation for button-first Telegram UX without breaking existing command-based runtime.

## Scope

- Add interaction map and callback contract docs for `Client` and `Master`.
- Implement shared callback router and validation layer in aiogram handlers.
- Add stale/invalid callback handling with deterministic `ru` responses.
- Preserve current command handlers as backward-compatible fallback.

## Included tasks

- T-001 - DONE
- T-002 - DONE

## Mergeability and runtime safety

- No DB schema change in this group.
- `docker compose up -d` remains the canonical local startup path.
- Existing smoke checks from `docs/04-delivery/local-dev.md` continue to pass unchanged.

## Acceptance checks

1. Callback payload parser rejects malformed payloads and returns deterministic `ru` reply.
2. Stale callback action path is covered by automated tests.
3. RBAC denials are logged/auditable for callback paths with no secret leakage.
4. Existing command-driven flows still work after merge.

## Validation commands

```bash
docker compose up -d --build
docker compose ps
.venv/bin/pytest -q
curl -fsS http://127.0.0.1:8080/health
```

## Group status

Status: DONE
Completed at: 2026-02-09

## Risks and mitigations

- Risk: callback payload growth beyond Telegram size constraints.
  - Mitigation: compact action identifiers + bounded payload schema from T-001.
- Risk: duplicated callback deliveries can trigger repeated writes.
  - Mitigation: reuse existing idempotency guard on write paths.
