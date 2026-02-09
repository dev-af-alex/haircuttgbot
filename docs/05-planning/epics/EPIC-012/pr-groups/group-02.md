# EPIC-012 / PR Group 02

## Objective

Implement button-first `Client` booking and cancellation journey on top of group-01 callback foundation, while keeping slash-command fallback intact.

## Scope

- Add callback actions for client flow: master -> service -> date -> slot -> confirm.
- Add callback actions for client cancellation from active future bookings list.
- Reuse existing booking/cancel services and preserve one-active-future-booking rule.
- Preserve existing command handlers and smoke path compatibility.

## Included tasks

- T-003 - DONE

## Mergeability and runtime safety

- No DB schema changes.
- `docker compose up -d` remains canonical local startup path.
- Existing smoke checks from `docs/04-delivery/local-dev.md` stay valid.

## Acceptance checks

1. Client can create booking via interactive callbacks without `/client_book`.
2. Client can cancel own active booking via interactive callbacks without `/client_cancel`.
3. One-active-future-booking guard remains enforced in callback path.
4. Existing command-driven flows remain operational.

## Validation commands

```bash
docker compose up -d --build
docker compose ps
.venv/bin/pytest -q
curl -fsS http://127.0.0.1:8080/health
```

## Group status

Status: DONE
Completed at: 2026-02-09
