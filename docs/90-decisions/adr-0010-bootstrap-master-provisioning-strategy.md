# ADR-0010: Bootstrap master provisioning strategy

Date: 2026-02-09
Status: Accepted
Deciders: Delivery engineering team

## Context

EPIC-013 requires the system to guarantee baseline RBAC records (`Client`, `Master`) and one bootstrap master, whose Telegram ID is configured via environment, on fresh and repeated startups. The current runtime already includes migration and seed paths, so we must choose where bootstrap responsibility lives to remain idempotent, observable, and safe for local/VM deployment.

## Decision

- Keep Alembic migrations schema-only (table/index/constraint ownership only).
- Keep bootstrap data provisioning in application seed flow (`app.db.seed.run_seed`) and execute it at API startup (`lifespan`) before Telegram runtime starts.
- Require `BOOTSTRAP_MASTER_TELEGRAM_ID` environment variable and fail fast when it is missing or invalid.
- Provisioning must be idempotent:
  - upsert roles (`Client`, `Master`);
  - upsert bootstrap user role to `Master`;
  - upsert bootstrap master profile with baseline working/lunch defaults.

## Alternatives considered

- Enforce bootstrap records exclusively in Alembic migrations.
- Enforce bootstrap records exclusively in application seed/startup path.
- Split responsibility: schema-level migration for invariant roles + startup reconciliation for bootstrap master identity.

## Consequences

- Positive:
  - deterministic startup state for local/VM runtime without manual SQL steps;
  - clear operational contract for bootstrap identity through one env key;
  - repeatable idempotent behavior across restarts and `python -m app.db.seed`.
- Negative:
  - startup now depends on valid bootstrap configuration and can fail early on misconfiguration;
  - API startup performs a small write transaction on each process start.
- Follow-up actions:
  - EPIC-013 group-02 will use this bootstrap identity as the authorization root for master add/remove flows;
  - runbooks must keep `BOOTSTRAP_MASTER_TELEGRAM_ID` documented for local and VM deployment paths.
