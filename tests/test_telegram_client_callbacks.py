from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from datetime import UTC

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
                    telegram_username TEXT,
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
                CREATE TABLE services (
                    id INTEGER PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    label_ru TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    is_active BOOLEAN NOT NULL
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
                INSERT INTO users (id, telegram_user_id, telegram_username, role_id)
                VALUES
                    (10, 1000001, 'owner_master', 2),
                    (20, 2000001, 'client_a', 1)
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
        conn.execute(
            text(
                """
                INSERT INTO services (code, label_ru, duration_minutes, is_active)
                VALUES
                    ('haircut', 'Стрижка', 30, 1),
                    ('beard', 'Борода', 30, 1),
                    ('haircut_beard', 'Стрижка + борода', 60, 1)
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


def _slot_tokens(callbacks: list[str]) -> set[str]:
    tokens: set[str] = set()
    for callback_data in callbacks:
        token = callback_data.rsplit("|", 1)[-1]
        datetime.strptime(token, "%Y%m%d%H%M").replace(tzinfo=UTC)
        tokens.add(token)
    return tokens


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
    assert "Мастер: Master Demo 1" in result.text
    assert "Мастер ID" not in result.text
    assert re.search(r"Слот: \d{2}\.\d{2}\.\d{4} \d{2}:\d{2}", result.text)

    result = router.handle(telegram_user_id=telegram_user_id, data="hb1|ccf")
    return result.text, slot_callbacks[0]


def test_client_interactive_booking_and_cancel_flow() -> None:
    router = TelegramCallbackRouter(_setup_flow_schema())
    router.seed_root_menu(telegram_user_id=2000001)

    booking_text, _ = _book_once(router, telegram_user_id=2000001)
    assert "успешно создана" in booking_text
    assert "Мастер: Master Demo 1" in booking_text
    assert "Мастер ID" not in booking_text
    assert "Слот:" in booking_text
    assert re.search(r"\d{2}:\d{2}-\d{2}:\d{2}", booking_text)


def test_start_menu_lands_client_directly_with_greeting() -> None:
    router = TelegramCallbackRouter(_setup_flow_schema())

    result = router.start_menu(telegram_user_id=2000001)

    assert "Добро пожаловать в барбершоп." in result.text
    assert "Меню клиента" in result.text


def test_client_flow_uses_fallback_master_name_when_profile_name_missing() -> None:
    engine = _setup_flow_schema()
    with engine.begin() as conn:
        conn.execute(text("UPDATE masters SET display_name = '' WHERE id = 1"))

    router = TelegramCallbackRouter(engine)
    router.seed_root_menu(telegram_user_id=2000001)

    router.handle(telegram_user_id=2000001, data="hb1|cm")
    result = router.handle(telegram_user_id=2000001, data="hb1|cb")
    assert "Выберите мастера" in result.text
    first_button = result.reply_markup.inline_keyboard[0][0]
    assert first_button.text == "Мастер (имя не указано)"

    result = router.handle(telegram_user_id=2000001, data=str(first_button.callback_data))
    service_callbacks = _callbacks_for_action(result.reply_markup, "css")
    result = router.handle(telegram_user_id=2000001, data=service_callbacks[0])
    date_callbacks = _callbacks_for_action(result.reply_markup, "csd")
    result = router.handle(telegram_user_id=2000001, data=date_callbacks[1])
    slot_callbacks = _callbacks_for_action(result.reply_markup, "csl")
    result = router.handle(telegram_user_id=2000001, data=slot_callbacks[0])
    assert "Мастер: Мастер (имя не указано)" in result.text
    result = router.handle(telegram_user_id=2000001, data="hb1|ccf")
    assert "успешно создана" in result.text

    result = router.handle(telegram_user_id=2000001, data="hb1|cc")
    cancel_pick_callbacks = _callbacks_for_action(result.reply_markup, "cci")
    assert cancel_pick_callbacks

    result = router.handle(telegram_user_id=2000001, data=cancel_pick_callbacks[0])
    assert "Подтвердите отмену" in result.text
    assert "Слот:" in result.text
    cancel_confirm_callbacks = _callbacks_for_action(result.reply_markup, "ccn")
    assert cancel_confirm_callbacks

    result = router.handle(telegram_user_id=2000001, data=cancel_confirm_callbacks[0])
    assert "успешно отменена" in result.text
    assert "Слот:" in result.text


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


def test_client_service_selection_controls_slot_granularity() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine)
    router.seed_root_menu(telegram_user_id=2000001)

    result = router.handle(telegram_user_id=2000001, data="hb1|cm")
    assert "Меню клиента" in result.text
    result = router.handle(telegram_user_id=2000001, data="hb1|cb")
    master_callbacks = _callbacks_for_action(result.reply_markup, "csm")
    assert master_callbacks
    result = router.handle(telegram_user_id=2000001, data=master_callbacks[0])
    service_callbacks = _callbacks_for_action(result.reply_markup, "css")
    haircut_callback = [item for item in service_callbacks if item.endswith("|haircut")]
    combo_callback = [item for item in service_callbacks if item.endswith("|haircut_beard")]
    assert haircut_callback and combo_callback

    result = router.handle(telegram_user_id=2000001, data=haircut_callback[0])
    date_callbacks = _callbacks_for_action(result.reply_markup, "csd")
    assert len(date_callbacks) >= 2
    date_token = date_callbacks[1].rsplit("|", 1)[-1]
    target_date = datetime.strptime(date_token, "%Y%m%d").replace(tzinfo=UTC)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO bookings (master_id, client_user_id, service_type, status, slot_start, slot_end)
                VALUES (1, 2999, 'haircut', 'active', :slot_start, :slot_end)
                """
            ),
            {
                "slot_start": target_date.replace(hour=10, minute=30),
                "slot_end": target_date.replace(hour=11, minute=0),
            },
        )

    result = router.handle(telegram_user_id=2000001, data=date_callbacks[1])
    haircut_slot_callbacks = _callbacks_for_action(result.reply_markup, "csl")
    assert haircut_slot_callbacks
    haircut_tokens = _slot_tokens(haircut_slot_callbacks)
    assert any(token.endswith("1000") for token in haircut_tokens)

    # Start a fresh booking attempt for 60-minute service.
    router = TelegramCallbackRouter(engine)
    router.seed_root_menu(telegram_user_id=2000001)
    result = router.handle(telegram_user_id=2000001, data="hb1|cm")
    result = router.handle(telegram_user_id=2000001, data="hb1|cb")
    master_callbacks = _callbacks_for_action(result.reply_markup, "csm")
    assert master_callbacks
    result = router.handle(telegram_user_id=2000001, data=master_callbacks[0])
    service_callbacks = _callbacks_for_action(result.reply_markup, "css")
    combo_callback = [item for item in service_callbacks if item.endswith("|haircut_beard")]
    assert combo_callback
    result = router.handle(telegram_user_id=2000001, data=combo_callback[0])
    date_callbacks = _callbacks_for_action(result.reply_markup, "csd")
    result = router.handle(telegram_user_id=2000001, data=date_callbacks[1])
    combo_slot_callbacks = _callbacks_for_action(result.reply_markup, "csl")
    assert combo_slot_callbacks
    combo_tokens = _slot_tokens(combo_slot_callbacks)
    assert all(not token.endswith("1000") for token in combo_tokens)


def test_client_confirm_rejects_stale_same_day_slot_token() -> None:
    router = TelegramCallbackRouter(_setup_flow_schema())
    router.seed_root_menu(telegram_user_id=2000001)

    result = router.handle(telegram_user_id=2000001, data="hb1|cm")
    assert "Меню клиента" in result.text

    result = router.handle(telegram_user_id=2000001, data="hb1|cb")
    master_callbacks = _callbacks_for_action(result.reply_markup, "csm")
    assert master_callbacks
    result = router.handle(telegram_user_id=2000001, data=master_callbacks[0])

    service_callbacks = _callbacks_for_action(result.reply_markup, "css")
    assert service_callbacks
    haircut_callback = [item for item in service_callbacks if item.endswith("|haircut")]
    assert haircut_callback
    result = router.handle(telegram_user_id=2000001, data=haircut_callback[0])
    date_callbacks = _callbacks_for_action(result.reply_markup, "csd")
    assert date_callbacks
    result = router.handle(telegram_user_id=2000001, data=date_callbacks[0])
    assert _callbacks_for_action(result.reply_markup, "csl")

    result = router.handle(telegram_user_id=2000001, data="hb1|csl|202602091000")
    assert "Подтвердите запись" in result.text

    result = router.handle(telegram_user_id=2000001, data="hb1|ccf")
    assert "уже недоступен" in result.text.lower()


def test_client_interactive_keyboards_keep_mobile_friendly_rows() -> None:
    router = TelegramCallbackRouter(_setup_flow_schema())
    router.seed_root_menu(telegram_user_id=2000001)

    result = router.handle(telegram_user_id=2000001, data="hb1|cm")
    client_menu_row_sizes = [len(row) for row in result.reply_markup.inline_keyboard]
    assert max(client_menu_row_sizes) <= 2

    result = router.handle(telegram_user_id=2000001, data="hb1|cb")
    master_row_sizes = [len(row) for row in result.reply_markup.inline_keyboard[:-1]]
    assert master_row_sizes
    assert max(master_row_sizes) <= 2

    master_callbacks = _callbacks_for_action(result.reply_markup, "csm")
    result = router.handle(telegram_user_id=2000001, data=master_callbacks[0])
    service_row_sizes = [len(row) for row in result.reply_markup.inline_keyboard[:-2]]
    assert service_row_sizes
    assert max(service_row_sizes) <= 2
