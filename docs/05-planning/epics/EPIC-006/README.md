# EPIC-006 — Master schedule management

Status: DONE

## Goal

Allow masters to manage schedule directly in Telegram: add manual bookings, set day-off periods, and change daily lunch break while preserving booking consistency.

## Scope

- Master flow to view upcoming schedule context and apply schedule changes.
- Manual booking creation by master for off-bot requests.
- Day-off block management that prevents client booking.
- Lunch break update management (default 13:00-14:00 remains baseline until changed).
- Availability recalculation consistency after schedule edits.

## Out of scope

- Observability and backup/alerting hardening (EPIC-007).
- VM rollout/rollback packaging (EPIC-008).

## Acceptance criteria

- Master can create manual booking for own schedule through Telegram flow.
- Master can create/update day-off periods and client booking excludes these intervals.
- Master can update lunch break window; updated lunch block is reflected in availability.
- Schedule edits cannot violate booking consistency (overlap/conflict checks remain enforced).
- `docker compose up -d --build` path remains healthy and local smoke covers schedule-change impact.

## Dependencies

- EPIC-004 booking flow baseline.
- EPIC-005 cancellation and notification baseline.

## Deliverables

- Master schedule management use cases and Telegram contracts.
- Persistence updates for day-off/lunch configuration and manual bookings.
- Tests for ownership, overlap validation, and availability recalculation.
- Updated delivery/API/planning docs for schedule management behavior.

## Planned PR groups

- Group 01: day-off management baseline + availability recalculation.
- Group 02: lunch break update flow + conflict validation.
- Group 03: manual booking flow + smoke/doc sync + acceptance hardening.

## Delivered

- Master day-off write path with ownership checks and immediate availability recalculation.
- Lunch break update flow with interval/duration/work-window validation and enforcement in availability/booking checks.
- Manual booking flow for offline requests with overlap/blocked-slot guardrails.
- Updated local smoke runbook covering day-off, lunch update, and manual-booking success/reject scenarios.

## Closure verification (2026-02-08)

- All tasks in `tasks.md` are `DONE`.
- All PR groups (`group-01`, `group-02`, `group-03`) are `DONE`.
- Local merge gates validated: `docker compose up -d --build`, updated smoke in `docs/04-delivery/local-dev.md`, and `.venv/bin/pytest -q`.
- Intentional deviations: CI status and security scans (Bandit, pip-audit, Gitleaks) are not executed locally and are expected on PR pipeline.
