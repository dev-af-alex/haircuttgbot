# Data model / storage

## 1) Core entities

- `roles`: role dictionary (`Client`, `Master`).
- `users`: Telegram identity + role mapping.
- `masters`: master profile and working window defaults (10:00-21:00, lunch 13:00-14:00).
- `bookings`: client-master time slot reservations and status lifecycle.
- `availability_blocks`: day-off, lunch-break, and manual unavailability windows.
- `audit_events`: security/booking lifecycle event log.

## 2) Storage decisions

- DB type: PostgreSQL 16.
- Migrations: Alembic (`alembic/`, `alembic.ini`) with revisioned schema changes.
- Backups: TODO (single VM backup cadence and restore validation in reliability epic).

## 3) Constraints and integrity rules

- `users.telegram_user_id` is unique.
- `masters.user_id` is unique (one master profile per user).
- `bookings` has partial unique index `ux_bookings_master_slot_active` to prevent two active bookings for same master+slot.
- `bookings.slot_end > bookings.slot_start` check.
- `availability_blocks.end_at > availability_blocks.start_at` check.

## 4) Data lifecycle

- Create/update/delete: role assignment, schedule changes, bookings, and cancellations are persisted in transactional tables.
- Retention: TODO (see `docs/02-nfr/privacy.md`).
