# EPIC-015 — PR Group 03

## Objective

Complete EPIC-015 by rolling readable-time formatting and mobile keyboard constraints through master/admin flows, expanding regression coverage, and synchronizing smoke documentation.

## Scope

- Apply shared `ru` time/date formatting to master-facing schedule/update/cancel texts.
- Apply mobile-friendly row-width constraints across master/admin keyboard builders.
- Expand callback regression tests for master/admin formatting and layout expectations.
- Synchronize local and VM Telegram validation notes with finalized readable-time/slot-range behavior.

## Tasks included

- T-006 Apply readable formatting to master schedule/update/cancel messages - DONE.
- T-007 Refactor master/admin keyboards for mobile usability - DONE.
- T-008 Expand regression tests for formatting and layout consistency - DONE.
- T-009 Sync smoke docs and complete epic closure checks - DONE.

## Mergeability and local-run guardrails

- Must remain mergeable by merge commit independently.
- No schema migration in this group.
- `docker compose up -d --build` remains healthy (`migrate` exit 0; runtime services healthy).
- Existing smoke and callback tests remain green after master/admin presentation updates.

## Acceptance checks

1. Master-facing schedule/day-off/lunch/manual/cancel flows return readable `ru` date/time output.
2. Master and bootstrap-admin keyboards keep phone-friendly row widths while preserving callback contracts.
3. Regression tests cover master/admin formatting and keyboard layout constraints.
4. Local and VM runbook Telegram validation steps reflect finalized slot range and readable-time checks.

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
