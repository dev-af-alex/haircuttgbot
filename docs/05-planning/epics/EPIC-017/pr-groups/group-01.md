# EPIC-017 — PR Group 01

## Objective

Deliver mergeable foundation for role-first `/start` behavior and master display-name decision policy before broader client-text rollout.

## Scope

- Create ADR stub for master display identity source/fallback policy.
- Implement direct role-panel landing on `/start` for resolved users.
- Replace command-list start text with localized barbershop greeting.
- Keep current booking/callback behavior unchanged outside entry flow.

## Tasks included

- T-001 Define master display identity policy ADR - DONE.
- T-002 Implement role-first `/start` routing baseline - DONE.
- T-003 Add localized greeting contract for `/start` - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable independently via merge commit.
- No destructive schema migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0, runtime services healthy).
- Existing smoke path remains executable after merge.

## Acceptance checks

1. ADR stub exists with explicit display-name fallback order and open decision points.
2. `/start` routes role-resolved users directly to role panel without `Главное меню` step.
3. `/start` text contract returns greeting-style localized message.
4. Canonical local smoke baseline passes without regressions.

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
