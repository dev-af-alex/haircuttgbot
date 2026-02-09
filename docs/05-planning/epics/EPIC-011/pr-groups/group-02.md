# EPIC-011 / PR Group 02

Status: DONE

## Objective

Implement real Telegram client/master command handlers in aiogram and map them to the existing booking and schedule service contracts with role checks.

## Included tasks

- T-003 — Implement client handler flow mapping to booking contracts
- T-004 — Implement master handler flow mapping to schedule/cancel contracts

## Why this grouping

- Delivers first end-to-end Telegram chat command path while reusing proven service-layer business rules.
- Keeps changes mergeable by focusing on handler mapping and authorization gates only.
- Preserves existing internal HTTP and smoke contracts.

## Acceptance checks

- Client commands cover start/master selection/slots/booking/cancel paths.
- Master commands cover cancel/day-off/lunch/manual-booking paths.
- Role enforcement is applied for command entry points.
- Automated tests cover handler-mapping/service-contract behavior and rejection paths.
- `docker compose up -d --build` and smoke path remain passing.

## Merge readiness gates

- Local compose runtime and smoke remain healthy.
- Security gates remain green.
- Docs are synchronized for new Telegram command interfaces.

## Task status

- T-003: DONE
- T-004: DONE

