# EPIC-021 — Configurable business timezone and temporal consistency

Status: DONE
Started: 2026-02-10
Roadmap source: `docs/05-planning/epics.md`

## Goal

Make booking/schedule time-dependent behavior run in a configurable business timezone (for example, `Europe/Moscow`) while preserving UTC-safe persistence and existing guardrail semantics.

## Scope

- Introduce validated business timezone runtime config.
- Enforce single policy for time conversion boundaries (Telegram/UI, domain logic, DB persistence).
- Keep storage and comparisons deterministic in UTC.
- Preserve current booking and schedule rules (lead-time guardrail, slot overlap, day-off/lunch constraints).
- Synchronize local and VM runbooks for timezone-aware smoke checks.

## Out of Scope

- Multi-branch timezone model with per-master/per-salon timezone in this epic.
- Changes to booking duration model or role model.
- Calendar sync with external providers.

## Dependencies

- EPIC-014 (service duration model and variable-slot engine)
- EPIC-016 (booking-time guardrails)
- EPIC-020 (baseline cleanup and admin stability)

## Planned PR Groups

- `group-01.md`: timezone policy baseline + config/ADR/domain primitives
- `group-02.md`: domain and Telegram flow timezone integration
- `group-03.md`: regression hardening + delivery docs synchronization

## ADR

- Accepted: `docs/90-decisions/adr-0018-business-timezone-policy.md`

## Delivered

- Введен конфиг `BUSINESS_TIMEZONE` с валидацией IANA и fail-fast startup-проверкой.
- Логика guardrails/availability/schedule/Telegram presentation переведена на business-timezone семантику при сохранении UTC в БД.
- Добавлены timezone и DST регрессии, синхронизированы `local-dev` и `deploy-vm` smoke-контракты.

## Epic Acceptance Target

- Runtime timezone is configurable and validated via IANA name (default `Europe/Moscow`).
- All user-facing and same-day guardrail behavior is evaluated in business timezone.
- DB persistence remains UTC with deterministic read/write conversion.
- Local/VM smoke and regression suite validate timezone-aware behavior and remain green.
