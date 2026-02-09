# EPIC-007 / PR Group 02

Status: DONE

## Objective

Ship backup/restore operational baseline: PostgreSQL logical backup runbook, clean-state restore rehearsal, and integrity verification steps.

## Included tasks

- T-004 - Implement PostgreSQL backup workflow + runbook
- T-005 - Validate restore rehearsal and data-integrity checks

## Why this grouping

- Delivers recovery readiness independently from alerting implementation.
- Keeps changes focused on operational documentation and verified commands.
- Provides a reusable restore procedure for incident response and release validation.

## Acceptance checks

- Runbook defines prerequisites, backup command, retention policy, and storage guidance.
- Restore rehearsal is documented against clean DB state with integrity checks.
- Local-dev smoke path references the backup/restore rehearsal document.

## Merge readiness gates

- `docker compose up -d --build` remains passing.
- Smoke test remains executable from `docs/04-delivery/local-dev.md`.
- Backup/restore commands are reproducible locally and documented in delivery docs.

## Task status

- T-004: DONE
- T-005: DONE
