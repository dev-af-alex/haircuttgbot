# EPIC-018 — PR Group 02

## Objective

Deliver production add-master behavior based on manual `@nickname` input while preserving RBAC, auditability, and remove-master stability.

## Scope

- Implement nickname-to-user resolution and assignment write-path semantics.
- Wire `Управление мастерами` add flow to nickname prompt and apply operations.
- Preserve bootstrap-only restrictions and existing master-admin observability outcomes.
- Keep remove-master path unchanged functionally.

## Tasks included

- T-004 Implement nickname-based master assignment service path - TODO.
- T-005 Wire Telegram admin add flow to manual nickname path - TODO.
- T-006 Preserve remove-master and backward compatibility checks - TODO.

## Mergeability and local-run guardrails

- Must remain mergeable independently via merge commit.
- No destructive schema migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0, runtime services healthy).
- Existing smoke path stays green with updated admin add-flow behavior.

## Acceptance checks

1. Bootstrap master can add master via manual `@nickname` input on success path.
2. Unknown and ambiguous nickname outcomes return deterministic localized feedback.
3. Bootstrap-only RBAC and master-admin audit/metrics events remain intact.
4. Remove-master flow remains operational and regression-safe.

## Validation commands

```bash
docker compose up -d --build
docker compose ps -a
.venv/bin/pytest -q
curl -fsS http://127.0.0.1:8080/health
```

## Group status

Status: TODO
