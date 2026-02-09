from __future__ import annotations

import sqlite3
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.telegram.callbacks import TelegramCallbackRouter

sqlite3.register_adapter(datetime, lambda value: value.isoformat())


def _setup_flow_schema() -> Engine:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)"))
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    telegram_user_id BIGINT UNIQUE NOT NULL,
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
                    service_type TEXT,
                    status TEXT NOT NULL,
                    cancellation_reason TEXT,
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
        conn.execute(text("INSERT INTO roles (id, name) VALUES (1, 'Client'), (2, 'Master')"))
        conn.execute(
            text(
                """
                INSERT INTO users (id, telegram_user_id, role_id)
                VALUES
                    (10, 1000001, 2),
                    (20, 2000001, 1)
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


def _callbacks_for_action(markup, action: str) -> list[str]:
    callbacks: list[str] = []
    for row in markup.inline_keyboard:
        for button in row:
            callback_data = button.callback_data
            if isinstance(callback_data, str) and callback_data.startswith(f"hb1|{action}"):
                callbacks.append(callback_data)
    return callbacks


def _book_once(router: TelegramCallbackRouter, *, telegram_user_id: int) -> tuple[str, str]:
    result = router.handle(telegram_user_id=telegram_user_id, data="hb1|cm")
    assert "Меню клиента" in result.text

    result = router.handle(telegram_user_id=telegram_user_id, data="hb1|cb")
    master_callbacks = _callbacks_for_action(result.reply_markup, "csm")
    assert master_callbacks

    result = router.handle(telegram_user_id=telegram_user_id, data=master_callbacks[0])
    service_callbacks = _callbacks_for_action(result.reply_markup, "css")
    assert service_callbacks

    result = router.handle(telegram_user_id=telegram_user_id, data=service_callbacks[0])
    date_callbacks = _callbacks_for_action(result.reply_markup, "csd")
    assert len(date_callbacks) >= 2

    # choose tomorrow to avoid flakiness when today's working hours have already passed
    result = router.handle(telegram_user_id=telegram_user_id, data=date_callbacks[1])
    slot_callbacks = _callbacks_for_action(result.reply_markup, "csl")
    assert slot_callbacks

    result = router.handle(telegram_user_id=telegram_user_id, data=slot_callbacks[0])
    assert "Подтвердите запись" in result.text

    result = router.handle(telegram_user_id=telegram_user_id, data="hb1|ccf")
    return result.text, slot_callbacks[0]


def test_client_interactive_booking_and_cancel_flow() -> None:
    router = TelegramCallbackRouter(_setup_flow_schema())
    router.seed_root_menu(telegram_user_id=2000001)

    booking_text, _ = _book_once(router, telegram_user_id=2000001)
    assert "успешно создана" in booking_text

    result = router.handle(telegram_user_id=2000001, data="hb1|cc")
    cancel_pick_callbacks = _callbacks_for_action(result.reply_markup, "cci")
    assert cancel_pick_callbacks

    result = router.handle(telegram_user_id=2000001, data=cancel_pick_callbacks[0])
    assert "Подтвердите отмену" in result.text
    cancel_confirm_callbacks = _callbacks_for_action(result.reply_markup, "ccn")
    assert cancel_confirm_callbacks

    result = router.handle(telegram_user_id=2000001, data=cancel_confirm_callbacks[0])
    assert "успешно отменена" in result.text


def test_client_interactive_flow_preserves_one_active_future_booking_limit() -> None:
    router = TelegramCallbackRouter(_setup_flow_schema())
    router.seed_root_menu(telegram_user_id=2000001)

    booking_text, _ = _book_once(router, telegram_user_id=2000001)
    assert "успешно создана" in booking_text

    result = router.handle(telegram_user_id=2000001, data="hb1|cb")
    master_callbacks = _callbacks_for_action(result.reply_markup, "csm")
    result = router.handle(telegram_user_id=2000001, data=master_callbacks[0])
    service_callbacks = _callbacks_for_action(result.reply_markup, "css")
    result = router.handle(telegram_user_id=2000001, data=service_callbacks[0])
    date_callbacks = _callbacks_for_action(result.reply_markup, "csd")
    result = router.handle(telegram_user_id=2000001, data=date_callbacks[1])
    slot_callbacks = _callbacks_for_action(result.reply_markup, "csl")
    result = router.handle(telegram_user_id=2000001, data=slot_callbacks[0])
    result = router.handle(telegram_user_id=2000001, data="hb1|ccf")

    assert "активная будущая запись" in result.text
