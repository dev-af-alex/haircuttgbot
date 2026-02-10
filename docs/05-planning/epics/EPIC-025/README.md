# EPIC-025 — Two-month booking horizon with paginated date navigation

Status: DONE
Started: 2026-02-10
Roadmap source: `docs/05-planning/epics.md`

## Goal

Allow `Client` and `Master` booking flows to select any date within a rolling 2-month horizon while preserving compact, navigable Telegram date UX (forward/back pages instead of full 2-month dump).

## Scope

- Extend booking date horizon in client and master manual booking flows to 2 months.
- Introduce paginated date picker contract in callback menus with forward/back actions.
- Keep stale callback handling deterministic and localized (`ru`).
- Preserve existing booking guardrails (overlaps, day-off/lunch, one-active-booking, timezone semantics).

## Out of Scope

- Changes to reminder policy window (still governed by EPIC-023 rules).
- New channels or non-Telegram UI.
- Cross-service architecture or deployment topology changes.

## Dependencies

- EPIC-012 (interactive callback UX baseline)
- EPIC-014 (duration-aware slots)
- EPIC-016 (time guardrails)
- EPIC-021 (business timezone semantics)

## Planned PR Groups

- `group-01.md`: paging contract + ADR + shared date-window helpers
- `group-02.md`: client and master callback integration for 2-month paginated navigation
- `group-03.md`: regression hardening + smoke/doc synchronization

## ADR

- Accepted: `docs/90-decisions/adr-0022-two-month-booking-horizon-and-date-picker-pagination.md`

## Epic Acceptance Target

- Client and master manual booking date selection support all days in rolling 2-month horizon.
- Date selection does not render the whole horizon at once; users can move pages forward/back.
- Forward/back page callbacks are idempotent and stale-safe.
- Existing functional/guardrail behavior remains unchanged and regression-covered.

## Delivered

- Implemented shared 60-day date pagination with explicit forward/back navigation callbacks for client and master manual booking flows.
- Preserved guardrails, stale/invalid callback determinism, and role boundaries under extended horizon.
- Added regression coverage for page boundaries, far-horizon booking success, and out-of-range page tokens.
- Updated SSOT docs for FR, callback contract, ADR status, and local smoke expectations.

## Merge Gates

- Local merge gates: satisfied (`.venv/bin/pytest -q`, `docker compose up -d --build`, seed, `/health`, `/metrics`, `docker compose down`).
- Intentional deviation: CI status and PR-time SAST/dependency/secrets scans were not re-run in this epic-close step.
