from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.telegram.commands import TelegramCommandService

sqlite3.register_adapter(datetime, lambda value: value.isoformat())


def _setup_schema() -> Engine:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)"))
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    telegram_user_id BIGINT UNIQUE NOT NULL,
                    telegram_username TEXT,
                    phone_number TEXT,
                    role_id INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE masters (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    display_name TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    work_start TEXT NOT NULL,
                    work_end TEXT NOT NULL,
                    lunch_start TEXT NOT NULL,
                    lunch_end TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE bookings (
                    id INTEGER PRIMARY KEY,
                    master_id INTEGER NOT NULL,
                    client_user_id INTEGER,
                    organizer_user_id INTEGER,
                    booking_group_key TEXT,
                    service_type TEXT,
                    status TEXT NOT NULL,
                    cancellation_reason TEXT,
                    manual_client_name TEXT,
                    client_username_snapshot TEXT,
                    client_phone_snapshot TEXT,
                    slot_start DATETIME NOT NULL,
                    slot_end DATETIME NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE availability_blocks (
                    id INTEGER PRIMARY KEY,
                    master_id INTEGER NOT NULL,
                    block_type TEXT,
                    start_at DATETIME NOT NULL,
                    end_at DATETIME NOT NULL,
                    reason TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE booking_reminders (
                    id INTEGER PRIMARY KEY,
                    booking_id INTEGER UNIQUE NOT NULL,
                    due_at DATETIME NOT NULL,
                    status TEXT NOT NULL,
                    sent_at DATETIME,
                    last_error TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(text("INSERT INTO roles (id, name) VALUES (1, 'Client'), (2, 'Master')"))
        conn.execute(
            text(
                """
                INSERT INTO users (id, telegram_user_id, telegram_username, role_id)
                VALUES
                    (10, 1000001, 'owner_master', 2),
                    (20, 2000001, 'client_a', 1),
                    (21, 2000002, 'client_b', 1)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO masters (id, user_id, display_name, is_active, work_start, work_end, lunch_start, lunch_end)
                VALUES
                    (1, 10, 'Master Demo 1', 1, '10:00:00', '21:00:00', '13:00:00', '14:00:00')
                """
            )
        )

    return engine


def test_client_flow_commands_are_role_protected() -> None:
    service = TelegramCommandService(_setup_schema())

    denied = service.client_start(telegram_user_id=1000001)
    assert "Недостаточно прав" in denied.text

    allowed = service.client_start(telegram_user_id=2000001)
    assert "Выберите мастера." in allowed.text
    assert "Master Demo 1" in allowed.text
    assert "1: Master Demo 1" not in allowed.text


def test_client_book_and_cancel_mapping_returns_notifications() -> None:
    engine = _setup_schema()
    service = TelegramCommandService(engine)

    booked = service.client_confirm(
        telegram_user_id=2000001,
        master_id=1,
        service_type="haircut",
        slot_start=datetime(2026, 2, 12, 10, 0, tzinfo=UTC),
    )
    assert "успешно создана" in booked.text
    assert len(booked.notifications) == 2

    with engine.connect() as conn:
        booking_id = conn.execute(text("SELECT id FROM bookings ORDER BY id DESC LIMIT 1")).scalar_one()

    cancelled = service.client_cancel(telegram_user_id=2000001, booking_id=int(booking_id))
    assert "успешно отменена" in cancelled.text
    assert len(cancelled.notifications) == 2


def test_master_schedule_commands_and_cancel_mapping() -> None:
    engine = _setup_schema()
    service = TelegramCommandService(engine)

    day_off = service.master_day_off(
        telegram_user_id=1000001,
        start_at=datetime(2026, 2, 16, 15, 0, tzinfo=UTC),
        end_at=datetime(2026, 2, 16, 16, 0, tzinfo=UTC),
    )
    assert "Выходной интервал сохранен" in day_off.text

    lunch = service.master_lunch(
        telegram_user_id=1000001,
        lunch_start=time.fromisoformat("18:00:00"),
        lunch_end=time.fromisoformat("19:00:00"),
    )
    assert "Обеденный перерыв обновлен" in lunch.text

    manual = service.master_manual(
        telegram_user_id=1000001,
        client_name="Offline Client",
        service_type="haircut",
        slot_start=datetime(2026, 2, 16, 12, 0, tzinfo=UTC),
    )
    assert "Ручная запись создана" in manual.text

    booked = service.client_confirm(
        telegram_user_id=2000001,
        master_id=1,
        service_type="haircut",
        slot_start=datetime(2026, 2, 17, 10, 0, tzinfo=UTC),
    )
    assert "успешно создана" in booked.text
    with engine.connect() as conn:
        booking_id = int(conn.execute(text("SELECT id FROM bookings ORDER BY id DESC LIMIT 1")).scalar_one())

    cancelled = service.master_cancel(
        telegram_user_id=1000001,
        booking_id=booking_id,
        reason="Непредвиденные обстоятельства",
    )
    assert "успешно отменена" in cancelled.text
    assert len(cancelled.notifications) == 2


def test_client_slots_command_formats_slots() -> None:
    service = TelegramCommandService(_setup_schema())

    result = service.client_slots(
        telegram_user_id=2000001,
        master_id=1,
        service_type="haircut_beard",
        on_date=date(2026, 2, 20),
    )

    assert "Выберите доступный слот." in result.text
    assert "2026-02-20T10:00:00+00:00" in result.text


def test_master_command_rejects_client_role() -> None:
    service = TelegramCommandService(_setup_schema())

    result = service.master_day_off(
        telegram_user_id=2000001,
        start_at=datetime(2026, 2, 16, 15, 0, tzinfo=UTC),
        end_at=datetime(2026, 2, 16, 16, 0, tzinfo=UTC),
    )

    assert "Недостаточно прав" in result.text


def test_help_rejects_unknown_user() -> None:
    service = TelegramCommandService(_setup_schema())

    result = service.help(telegram_user_id=9999999)

    assert "Пользователь не найден" in result.text
