# EPIC-022 — Informative booking/cancellation notifications and manual-client text in master booking

Status: DONE
Started: 2026-02-10
Roadmap source: `docs/05-planning/epics.md`

## Goal

Make booking/cancellation notifications context-rich for both roles and allow master manual booking flow to accept arbitrary client text.

## Scope

- Enrich master booking-created notifications with client identity context and exact booking date/time.
- Enrich client cancellation notifications (master-initiated cancel) with exact cancelled booking date/time.
- Support free-text client input in manual booking flow and preserve it for schedule/notification rendering.
- Keep existing RBAC, cancellation-reason requirement, and readable `ru` datetime formatting.
- Keep docker-compose local run and VM deployment smoke path stable.

## Out of Scope

- Background reminder scheduling (planned in EPIC-023).
- Large-scale query/index optimization (planned in EPIC-024).
- New external channels beyond Telegram.

## Dependencies

- EPIC-005 (cancellation and notification flow baseline)
- EPIC-006 (master schedule/manual booking baseline)
- EPIC-015 (readable time/text formatting baseline)
- EPIC-021 (business timezone consistency)

## Planned PR Groups

- `group-01.md`: notification identity contract + data model baseline
- `group-02.md`: Telegram flow integration for informative notifications and manual client text
- `group-03.md`: regression hardening + delivery docs synchronization

## ADR

- Accepted: `docs/90-decisions/adr-0019-notification-context-and-manual-client-reference-policy.md`

## Delivered

- Added booking/user data fields for notification context (`manual_client_name`, username/phone snapshots, optional `users.phone_number`) with migration `20260210_0004`.
- Updated notification builder so master booking-created notifications include client identity context and exact slot datetime; master-cancel notification to client now includes exact cancelled slot datetime.
- Reworked master manual booking callback flow: after slot selection bot requires free-text client input and persists it into booking; confirmations and schedule view render this client context.
- Added regression coverage for informative notifications, manual-client text handling, and phone redaction behavior in observability logs.
- Synchronized delivery docs (`local-dev`, `deploy-vm`) and architecture docs (`apis`, `data`, `requirements`, `security`) with the new contracts.

## Epic Acceptance Target

- Master booking-created notification includes client identity context (Telegram nickname when available, plus phone if available) and exact booking date/time.
- Client cancellation notification from master action includes exact cancelled booking date/time in readable localized format.
- Manual booking supports arbitrary client free-text and surfaces it in schedule/notification outputs deterministically.
- Local/VM smoke and regression checks remain green with updated notification contracts.

## Merge-Gate Notes

- Local merge gates satisfied: docker-compose up/down, smoke-related checks, and focused/full regression test suites.
- Intentional deviation: CI-only gates (Bandit, pip-audit, Gitleaks, PR reviewer verification) were not executed in this local close step and must pass in PR pipeline.
