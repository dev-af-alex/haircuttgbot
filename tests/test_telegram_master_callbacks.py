from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime, time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.telegram.callbacks import TelegramCallbackRouter

sqlite3.register_adapter(datetime, lambda value: value.isoformat())
sqlite3.register_adapter(time, lambda value: value.isoformat())


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
                    (11, 1000002, 'worker_master', 2),
                    (20, 2000001, 'client_a', 1),
                    (21, 2000002, 'candidate_master', 1)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO masters (id, user_id, display_name, is_active, work_start, work_end, lunch_start, lunch_end)
                VALUES
                    (1, 10, 'Master Demo 1', 1, '10:00:00', '21:00:00', '13:00:00', '14:00:00'),
                    (2, 11, 'Master Demo 2', 1, '10:00:00', '21:00:00', '13:00:00', '14:00:00')
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


def _create_client_booking(engine: Engine, *, slot_start: datetime) -> int:
    with engine.begin() as conn:
        booking_id = conn.execute(
            text(
                """
                INSERT INTO bookings (master_id, client_user_id, service_type, slot_start, slot_end, status)
                VALUES (1, 20, 'haircut', :slot_start, :slot_end, 'active')
                RETURNING id
                """
            ),
            {
                "slot_start": slot_start,
                "slot_end": slot_start.replace(hour=slot_start.hour + 1),
            },
        ).scalar_one()
    return int(booking_id)


def test_master_interactive_schedule_dayoff_lunch_manual_flow() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine)
    router.seed_root_menu(telegram_user_id=1000001)

    result = router.handle(telegram_user_id=1000001, data="hb1|mm")
    assert "Меню мастера" in result.text

    result = router.handle(telegram_user_id=1000001, data="hb1|msv")
    assert "Выберите дату для просмотра расписания" in result.text
    schedule_date_callbacks = _callbacks_for_action(result.reply_markup, "msv")
    assert len(schedule_date_callbacks) >= 2
    result = router.handle(telegram_user_id=1000001, data=schedule_date_callbacks[1])
    assert "Расписание на" in result.text
    assert re.search(r"Обед: \d{2}:\d{2} - \d{2}:\d{2}", result.text)

    result = router.handle(telegram_user_id=1000001, data="hb1|msd")
    day_off_callbacks = _callbacks_for_action(result.reply_markup, "msu")
    assert day_off_callbacks

    result = router.handle(telegram_user_id=1000001, data=day_off_callbacks[0])
    assert "Выходной интервал" in result.text
    assert "Дата:" in result.text
    assert "Интервал:" in result.text

    result = router.handle(telegram_user_id=1000001, data="hb1|mlm")
    lunch_callbacks = _callbacks_for_action(result.reply_markup, "mls")
    assert lunch_callbacks

    result = router.handle(telegram_user_id=1000001, data=lunch_callbacks[-1])
    assert "Обеденный перерыв обновлен" in result.text
    assert "Новый интервал:" in result.text

    result = router.handle(telegram_user_id=1000001, data="hb1|msb")
    service_callbacks = _callbacks_for_action(result.reply_markup, "mbs")
    assert service_callbacks

    result = router.handle(telegram_user_id=1000001, data=service_callbacks[0])
    date_callbacks = _callbacks_for_action(result.reply_markup, "mbd")
    assert len(date_callbacks) >= 2

    result = router.handle(telegram_user_id=1000001, data=date_callbacks[1])
    slot_callbacks = _callbacks_for_action(result.reply_markup, "mbl")
    assert slot_callbacks
    assert any(item.rsplit("|", 1)[-1].endswith("30") for item in slot_callbacks)

    result = router.handle(telegram_user_id=1000001, data=slot_callbacks[0])
    assert "Подтвердите ручную запись" in result.text
    assert re.search(r"Слот: \d{2}\.\d{2}\.\d{4} \d{2}:\d{2}", result.text)

    result = router.handle(telegram_user_id=1000001, data="hb1|mbc")
    assert "Ручная запись создана" in result.text
    assert "Слот:" in result.text
    assert re.search(r"\d{2}:\d{2}-\d{2}:\d{2}", result.text)


def test_start_menu_lands_master_directly_with_greeting() -> None:
    router = TelegramCallbackRouter(_setup_flow_schema())

    result = router.start_menu(telegram_user_id=1000001)

    assert "Добро пожаловать в барбершоп." in result.text
    assert "Меню мастера" in result.text


def test_master_day_off_rejects_occupied_date() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine)
    router.seed_root_menu(telegram_user_id=1000001)

    _create_client_booking(
        engine,
        slot_start=datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
    )

    result = router.handle(telegram_user_id=1000001, data="hb1|mm")
    assert "Меню мастера" in result.text

    result = router.handle(telegram_user_id=1000001, data="hb1|msd")
    day_off_callbacks = _callbacks_for_action(result.reply_markup, "msu")
    assert day_off_callbacks

    target = [item for item in day_off_callbacks if item.endswith("|20260210")]
    assert target
    result = router.handle(telegram_user_id=1000001, data=target[0])
    assert "уже есть активные записи" in result.text.lower()


def test_master_interactive_cancel_requires_reason_and_sends_notifications() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine)
    router.seed_root_menu(telegram_user_id=1000001)

    _create_client_booking(
        engine,
        slot_start=datetime(2026, 2, 20, 10, 0, tzinfo=UTC),
    )

    result = router.handle(telegram_user_id=1000001, data="hb1|mm")
    assert "Меню мастера" in result.text

    result = router.handle(telegram_user_id=1000001, data="hb1|msc")
    cancel_pick_callbacks = _callbacks_for_action(result.reply_markup, "mci")
    assert cancel_pick_callbacks

    result = router.handle(telegram_user_id=1000001, data=cancel_pick_callbacks[0])
    reason_callbacks = _callbacks_for_action(result.reply_markup, "mcr")
    assert reason_callbacks
    assert "Слот:" in result.text
    assert "Услуга:" in result.text

    # confirm without choosing reason is stale
    stale = router.handle(telegram_user_id=1000001, data="hb1|mcn")
    assert "устарела" in stale.text

    result = router.handle(telegram_user_id=1000001, data=reason_callbacks[0])
    assert "Подтвердите отмену" in result.text
    assert "Слот:" in result.text

    result = router.handle(telegram_user_id=1000001, data="hb1|mcn")
    assert "успешно отменена" in result.text
    assert "Слот:" in result.text
    assert "Причина:" in result.text
    assert len(result.notifications) == 2


def test_bootstrap_master_can_add_and_remove_other_masters() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine, bootstrap_master_telegram_user_id=1000001)
    router.seed_root_menu(telegram_user_id=1000001)

    result = router.handle(telegram_user_id=1000001, data="hb1|mm")
    manage_callbacks = _callbacks_for_action(result.reply_markup, "mam")
    assert manage_callbacks

    result = router.handle(telegram_user_id=1000001, data=manage_callbacks[0])
    assert "Управление мастерами" in result.text

    result = router.handle(telegram_user_id=1000001, data="hb1|maa")
    assert "@nickname" in result.text

    result = router.handle_text(telegram_user_id=1000001, text_value="@candidate_master")
    assert result is not None
    assert "добавлен" in result.text.lower() or "активен" in result.text.lower()

    with engine.begin() as conn:
        role_name = conn.execute(
            text(
                """
                SELECT r.name
                FROM users u
                JOIN roles r ON r.id = u.role_id
                WHERE u.telegram_user_id = 2000002
                """
            )
        ).scalar_one()
        assert role_name == "Master"

        is_active = conn.execute(
            text(
                """
                SELECT m.is_active
                FROM masters m
                JOIN users u ON u.id = m.user_id
                WHERE u.telegram_user_id = 2000002
                """
            )
        ).scalar_one()
        assert bool(is_active) is True

    result = router.handle(telegram_user_id=1000001, data="hb1|mad")
    remove_callbacks = _callbacks_for_action(result.reply_markup, "mar")
    assert remove_callbacks
    remove_target = [item for item in remove_callbacks if item.endswith("|1000002")]
    assert remove_target
    result = router.handle(telegram_user_id=1000001, data=remove_target[0])
    assert "удален" in result.text.lower() or "неактив" in result.text.lower()

    with engine.begin() as conn:
        is_active = conn.execute(
            text(
                """
                SELECT m.is_active
                FROM masters m
                JOIN users u ON u.id = m.user_id
                WHERE u.telegram_user_id = 1000002
                """
            )
        ).scalar_one()
        assert bool(is_active) is False


def test_non_bootstrap_master_is_denied_for_master_admin_callbacks() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine, bootstrap_master_telegram_user_id=1000001)
    router.seed_root_menu(telegram_user_id=1000002)

    result = router.handle(telegram_user_id=1000002, data="hb1|mam")
    assert "Недостаточно прав" in result.text

    result = router.handle(telegram_user_id=1000002, data="hb1|man")
    assert "Недостаточно прав" in result.text


def test_master_and_admin_keyboards_keep_mobile_friendly_rows() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine, bootstrap_master_telegram_user_id=1000001)
    router.seed_root_menu(telegram_user_id=1000001)

    result = router.handle(telegram_user_id=1000001, data="hb1|mm")
    master_menu_row_sizes = [len(row) for row in result.reply_markup.inline_keyboard]
    assert max(master_menu_row_sizes) <= 2

    result = router.handle(telegram_user_id=1000001, data="hb1|msb")
    service_row_sizes = [len(row) for row in result.reply_markup.inline_keyboard[:-1]]
    assert service_row_sizes
    assert max(service_row_sizes) <= 2

    router.handle(telegram_user_id=1000001, data="hb1|mr")
    result = router.handle(telegram_user_id=1000001, data="hb1|mlm")
    lunch_row_sizes = [len(row) for row in result.reply_markup.inline_keyboard[:-1]]
    assert lunch_row_sizes
    assert max(lunch_row_sizes) <= 2

    router.handle(telegram_user_id=1000001, data="hb1|mr")
    result = router.handle(telegram_user_id=1000001, data="hb1|mam")
    admin_menu_row_sizes = [len(row) for row in result.reply_markup.inline_keyboard]
    assert max(admin_menu_row_sizes) <= 2

    result = router.handle(telegram_user_id=1000001, data="hb1|maa")
    add_row_sizes = [len(row) for row in result.reply_markup.inline_keyboard]
    assert add_row_sizes
    assert max(add_row_sizes) <= 2


def test_bootstrap_master_add_by_nickname_rejects_invalid_unknown_and_ambiguous() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine, bootstrap_master_telegram_user_id=1000001)
    router.seed_root_menu(telegram_user_id=1000001)

    router.handle(telegram_user_id=1000001, data="hb1|mm")
    router.handle(telegram_user_id=1000001, data="hb1|mam")
    router.handle(telegram_user_id=1000001, data="hb1|maa")

    invalid = router.handle_text(telegram_user_id=1000001, text_value="candidate_master")
    assert invalid is not None
    assert "неверный формат" in invalid.text.lower()

    unknown = router.handle_text(telegram_user_id=1000001, text_value="@unknown_user")
    assert unknown is not None
    assert "не найден" in unknown.text.lower()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO users (id, telegram_user_id, telegram_username, role_id)
                VALUES (31, 2000003, 'dup_nick', 1), (32, 2000004, 'dup_nick', 1)
                """
            )
        )
    ambiguous = router.handle_text(telegram_user_id=1000001, text_value="@dup_nick")
    assert ambiguous is not None
    assert "неоднознач" in ambiguous.text.lower()


def test_bootstrap_master_can_rename_master_display_name() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine, bootstrap_master_telegram_user_id=1000001)
    router.seed_root_menu(telegram_user_id=1000001)

    router.handle(telegram_user_id=1000001, data="hb1|mm")
    router.handle(telegram_user_id=1000001, data="hb1|mam")
    result = router.handle(telegram_user_id=1000001, data="hb1|man")
    rename_callbacks = _callbacks_for_action(result.reply_markup, "max")
    assert rename_callbacks
    target = [item for item in rename_callbacks if item.endswith("|1000002")]
    assert target

    prompt = router.handle(telegram_user_id=1000001, data=target[0])
    assert "Введите новое имя мастера" in prompt.text

    applied = router.handle_text(telegram_user_id=1000001, text_value="Master Renamed")
    assert applied is not None
    assert "обновлено" in applied.text.lower()

    with engine.begin() as conn:
        display_name = conn.execute(
            text(
                """
                SELECT m.display_name
                FROM masters m
                JOIN users u ON u.id = m.user_id
                WHERE u.telegram_user_id = 1000002
                """
            )
        ).scalar_one()
        assert display_name == "Master Renamed"


def test_bootstrap_master_rename_rejects_invalid_name_input() -> None:
    engine = _setup_flow_schema()
    router = TelegramCallbackRouter(engine, bootstrap_master_telegram_user_id=1000001)
    router.seed_root_menu(telegram_user_id=1000001)

    router.handle(telegram_user_id=1000001, data="hb1|mm")
    router.handle(telegram_user_id=1000001, data="hb1|mam")
    start = router.handle(telegram_user_id=1000001, data="hb1|man")
    rename_callbacks = _callbacks_for_action(start.reply_markup, "max")
    assert rename_callbacks
    router.handle(telegram_user_id=1000001, data=rename_callbacks[0])

    rejected = router.handle_text(telegram_user_id=1000001, text_value=" ")
    assert rejected is not None
    assert "некоррект" in rejected.text.lower()
