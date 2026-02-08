from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.booking.availability import AvailabilityService
from app.booking.cancel_booking import BookingCancellationService
from app.booking.contracts import (
    BOOKING_STATUS_ACTIVE,
    BOOKING_STATUS_CANCELLED_BY_CLIENT,
    BOOKING_STATUS_CANCELLED_BY_MASTER,
    can_transition_booking_status,
    is_cancellation_reason_required,
)
from app.booking.create_booking import BookingService
from app.booking.flow import TelegramBookingFlowService
from app.booking.schedule import (
    MasterDayOffCommand,
    MasterLunchBreakCommand,
    MasterManualBookingCommand,
    MasterScheduleService,
)
from app.booking.service_options import (
    SERVICE_OPTION_CODES,
    SERVICE_OPTION_LABELS_RU,
    list_service_options,
)

sqlite3.register_adapter(datetime, lambda value: value.isoformat())


def _setup_availability_schema() -> Engine:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE masters (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
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

        conn.execute(
            text(
                """
                INSERT INTO masters (id, user_id, is_active, work_start, work_end, lunch_start, lunch_end)
                VALUES (1, 10, 1, '10:00:00', '21:00:00', '13:00:00', '14:00:00')
                """
            )
        )

    return engine


def _setup_telegram_flow_schema() -> Engine:
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
                    (11, 1000002, 2),
                    (20, 2000001, 1),
                    (21, 2000002, 1)
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

    return engine


def test_service_options_contract() -> None:
    options = list_service_options()

    assert [item["code"] for item in options] == list(SERVICE_OPTION_CODES)
    assert {item["code"]: item["label"] for item in options} == SERVICE_OPTION_LABELS_RU


def test_availability_excludes_past_lunch_booking_and_blocks() -> None:
    engine = _setup_availability_schema()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO bookings (master_id, status, slot_start, slot_end)
                VALUES (1, 'active', :slot_start, :slot_end)
                """
            ),
            {
                "slot_start": datetime(2026, 2, 9, 11, 0, tzinfo=UTC),
                "slot_end": datetime(2026, 2, 9, 12, 0, tzinfo=UTC),
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO availability_blocks (master_id, start_at, end_at)
                VALUES
                    (1, :block_1_start, :block_1_end),
                    (1, :block_2_start, :block_2_end)
                """
            ),
            {
                "block_1_start": datetime(2026, 2, 9, 15, 0, tzinfo=UTC),
                "block_1_end": datetime(2026, 2, 9, 16, 0, tzinfo=UTC),
                "block_2_start": datetime(2026, 2, 9, 18, 0, tzinfo=UTC),
                "block_2_end": datetime(2026, 2, 9, 20, 0, tzinfo=UTC),
            },
        )

    service = AvailabilityService(engine)
    slots = service.list_slots(
        master_id=1,
        on_date=date(2026, 2, 9),
        now=datetime(2026, 2, 9, 10, 30, tzinfo=UTC),
    )

    starts = [slot.start_at.strftime("%H:%M") for slot in slots]

    assert starts == ["12:00", "14:00", "16:00", "17:00", "20:00"]


def test_availability_half_open_overlap_boundaries() -> None:
    engine = _setup_availability_schema()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO availability_blocks (master_id, start_at, end_at)
                VALUES
                    (1, :block_1_start, :block_1_end),
                    (1, :block_2_start, :block_2_end)
                """
            ),
            {
                "block_1_start": datetime(2026, 2, 10, 14, 0, tzinfo=UTC),
                "block_1_end": datetime(2026, 2, 10, 15, 0, tzinfo=UTC),
                "block_2_start": datetime(2026, 2, 10, 16, 0, tzinfo=UTC),
                "block_2_end": datetime(2026, 2, 10, 17, 0, tzinfo=UTC),
            },
        )

    service = AvailabilityService(engine)
    slots = service.list_slots(master_id=1, on_date=date(2026, 2, 10), now=datetime(2026, 2, 10, 9, 0, tzinfo=UTC))

    starts = [slot.start_at.strftime("%H:%M") for slot in slots]

    assert "15:00" in starts
    assert "16:00" not in starts


def test_create_booking_success() -> None:
    engine = _setup_availability_schema()

    service = BookingService(engine)
    result = service.create_booking(
        master_id=1,
        client_user_id=5001,
        service_type="haircut",
        slot_start=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
        now=datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
    )

    assert result.created is True
    assert result.booking_id is not None

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT master_id, client_user_id, service_type, status
                FROM bookings
                WHERE id = :id
                """
            ),
            {"id": result.booking_id},
        ).mappings().one()

    assert row["master_id"] == 1
    assert row["client_user_id"] == 5001
    assert row["service_type"] == "haircut"
    assert row["status"] == "active"


def test_create_booking_rejects_overlapping_master_slot() -> None:
    engine = _setup_availability_schema()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO bookings (master_id, client_user_id, service_type, status, slot_start, slot_end)
                VALUES (1, 9001, 'beard', 'active', :slot_start, :slot_end)
                """
            ),
            {
                "slot_start": datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
                "slot_end": datetime(2026, 2, 11, 11, 0, tzinfo=UTC),
            },
        )

    service = BookingService(engine)
    result = service.create_booking(
        master_id=1,
        client_user_id=5001,
        service_type="haircut",
        slot_start=datetime(2026, 2, 11, 10, 30, tzinfo=UTC),
        now=datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
    )

    assert result.created is False
    assert "недоступен" in result.message


def test_create_booking_rejects_second_future_booking_for_client() -> None:
    engine = _setup_availability_schema()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO bookings (master_id, client_user_id, service_type, status, slot_start, slot_end)
                VALUES (1, 5001, 'beard', 'active', :slot_start, :slot_end)
                """
            ),
            {
                "slot_start": datetime(2026, 2, 11, 12, 0, tzinfo=UTC),
                "slot_end": datetime(2026, 2, 11, 13, 0, tzinfo=UTC),
            },
        )

    service = BookingService(engine)
    result = service.create_booking(
        master_id=1,
        client_user_id=5001,
        service_type="haircut",
        slot_start=datetime(2026, 2, 11, 16, 0, tzinfo=UTC),
        now=datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
    )

    assert result.created is False
    assert "активная будущая" in result.message


def test_cancellation_contract_baseline() -> None:
    assert can_transition_booking_status(
        current_status=BOOKING_STATUS_ACTIVE,
        target_status=BOOKING_STATUS_CANCELLED_BY_CLIENT,
    )
    assert can_transition_booking_status(
        current_status=BOOKING_STATUS_ACTIVE,
        target_status=BOOKING_STATUS_CANCELLED_BY_MASTER,
    )
    assert not can_transition_booking_status(
        current_status=BOOKING_STATUS_CANCELLED_BY_CLIENT,
        target_status=BOOKING_STATUS_CANCELLED_BY_CLIENT,
    )
    assert not is_cancellation_reason_required(target_status=BOOKING_STATUS_CANCELLED_BY_CLIENT)
    assert is_cancellation_reason_required(target_status=BOOKING_STATUS_CANCELLED_BY_MASTER)


def test_client_cancel_success() -> None:
    engine = _setup_availability_schema()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO bookings (id, master_id, client_user_id, service_type, status, slot_start, slot_end)
                VALUES (41, 1, 5001, 'haircut', 'active', :slot_start, :slot_end)
                """
            ),
            {
                "slot_start": datetime(2026, 2, 12, 10, 0, tzinfo=UTC),
                "slot_end": datetime(2026, 2, 12, 11, 0, tzinfo=UTC),
            },
        )

    service = BookingCancellationService(engine)
    result = service.cancel_by_client(
        booking_id=41,
        client_user_id=5001,
        now=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
    )
    assert result.cancelled is True
    assert result.booking_id == 41

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT status, cancellation_reason FROM bookings WHERE id = 41"),
        ).mappings().one()
    assert row["status"] == "cancelled_by_client"
    assert row["cancellation_reason"] is None


def test_client_cancel_rejects_non_owner_and_past_or_inactive() -> None:
    engine = _setup_availability_schema()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO bookings (id, master_id, client_user_id, service_type, status, slot_start, slot_end)
                VALUES
                    (42, 1, 5001, 'haircut', 'active', :future_start, :future_end),
                    (43, 1, 5001, 'beard', 'active', :past_start, :past_end),
                    (44, 1, 5001, 'beard', 'cancelled_by_client', :inactive_start, :inactive_end)
                """
            ),
            {
                "future_start": datetime(2026, 2, 12, 10, 0, tzinfo=UTC),
                "future_end": datetime(2026, 2, 12, 11, 0, tzinfo=UTC),
                "past_start": datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
                "past_end": datetime(2026, 2, 10, 11, 0, tzinfo=UTC),
                "inactive_start": datetime(2026, 2, 12, 12, 0, tzinfo=UTC),
                "inactive_end": datetime(2026, 2, 12, 13, 0, tzinfo=UTC),
            },
        )

    service = BookingCancellationService(engine)
    non_owner = service.cancel_by_client(
        booking_id=42,
        client_user_id=6001,
        now=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
    )
    assert non_owner.cancelled is False

    past = service.cancel_by_client(
        booking_id=43,
        client_user_id=5001,
        now=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
    )
    assert past.cancelled is False

    inactive = service.cancel_by_client(
        booking_id=44,
        client_user_id=5001,
        now=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
    )
    assert inactive.cancelled is False


def test_master_cancel_requires_reason_and_enforces_ownership() -> None:
    engine = _setup_availability_schema()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO bookings (id, master_id, client_user_id, service_type, status, slot_start, slot_end)
                VALUES (45, 1, 5001, 'haircut', 'active', :slot_start, :slot_end)
                """
            ),
            {
                "slot_start": datetime(2026, 2, 12, 10, 0, tzinfo=UTC),
                "slot_end": datetime(2026, 2, 12, 11, 0, tzinfo=UTC),
            },
        )

    service = BookingCancellationService(engine)
    no_reason = service.cancel_by_master(
        booking_id=45,
        master_user_id=10,
        reason="   ",
        now=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
    )
    assert no_reason.cancelled is False
    assert "причину" in no_reason.message.lower()

    wrong_owner = service.cancel_by_master(
        booking_id=45,
        master_user_id=999,
        reason="Тестовая причина",
        now=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
    )
    assert wrong_owner.cancelled is False


def test_master_cancel_success_persists_reason() -> None:
    engine = _setup_availability_schema()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO bookings (id, master_id, client_user_id, service_type, status, slot_start, slot_end)
                VALUES (46, 1, 5001, 'haircut', 'active', :slot_start, :slot_end)
                """
            ),
            {
                "slot_start": datetime(2026, 2, 12, 12, 0, tzinfo=UTC),
                "slot_end": datetime(2026, 2, 12, 13, 0, tzinfo=UTC),
            },
        )

    service = BookingCancellationService(engine)
    result = service.cancel_by_master(
        booking_id=46,
        master_user_id=10,
        reason="Мастер заболел",
        now=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
    )
    assert result.cancelled is True
    assert result.cancellation_reason == "Мастер заболел"

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT status, cancellation_reason FROM bookings WHERE id = 46"),
        ).mappings().one()
    assert row["status"] == "cancelled_by_master"
    assert row["cancellation_reason"] == "Мастер заболел"


def test_master_schedule_contracts_and_ownership_resolution() -> None:
    engine = _setup_telegram_flow_schema()
    service = MasterScheduleService(engine)

    day_off = MasterDayOffCommand(
        start_at=datetime(2026, 2, 14, 15, 0, tzinfo=UTC),
        end_at=datetime(2026, 2, 14, 17, 0, tzinfo=UTC),
    )
    lunch = MasterLunchBreakCommand(lunch_start=datetime.strptime("13:00", "%H:%M").time(), lunch_end=datetime.strptime("14:00", "%H:%M").time())
    manual = MasterManualBookingCommand(
        client_name="Client Demo",
        service_type="haircut",
        slot_start=datetime(2026, 2, 14, 12, 0, tzinfo=UTC),
    )

    assert day_off.block_id is None
    assert lunch.lunch_start.hour == 13
    assert manual.client_name == "Client Demo"

    context = service.resolve_context(master_telegram_user_id=1000001)
    assert context is not None
    assert context.master_id == 1


def test_master_day_off_create_and_update_affect_availability() -> None:
    engine = _setup_telegram_flow_schema()
    service = MasterScheduleService(engine)
    availability = AvailabilityService(engine)

    created = service.upsert_day_off(
        master_telegram_user_id=1000001,
        command=MasterDayOffCommand(
            start_at=datetime(2026, 2, 14, 15, 0, tzinfo=UTC),
            end_at=datetime(2026, 2, 14, 17, 0, tzinfo=UTC),
        ),
    )
    assert created.applied is True
    assert created.created is True
    assert created.block_id is not None

    slots_after_create = availability.list_slots(
        master_id=1,
        on_date=date(2026, 2, 14),
        now=datetime(2026, 2, 14, 9, 0, tzinfo=UTC),
    )
    starts_after_create = {slot.start_at.strftime("%H:%M") for slot in slots_after_create}
    assert "15:00" not in starts_after_create
    assert "16:00" not in starts_after_create

    updated = service.upsert_day_off(
        master_telegram_user_id=1000001,
        command=MasterDayOffCommand(
            block_id=created.block_id,
            start_at=datetime(2026, 2, 14, 16, 0, tzinfo=UTC),
            end_at=datetime(2026, 2, 14, 18, 0, tzinfo=UTC),
        ),
    )
    assert updated.applied is True
    assert updated.created is False

    slots_after_update = availability.list_slots(
        master_id=1,
        on_date=date(2026, 2, 14),
        now=datetime(2026, 2, 14, 9, 0, tzinfo=UTC),
    )
    starts_after_update = {slot.start_at.strftime("%H:%M") for slot in slots_after_update}
    assert "15:00" in starts_after_update
    assert "16:00" not in starts_after_update
    assert "17:00" not in starts_after_update


def test_master_day_off_rejects_invalid_conflict_and_non_owner_update() -> None:
    engine = _setup_telegram_flow_schema()
    service = MasterScheduleService(engine)

    invalid = service.upsert_day_off(
        master_telegram_user_id=1000001,
        command=MasterDayOffCommand(
            start_at=datetime(2026, 2, 14, 17, 0, tzinfo=UTC),
            end_at=datetime(2026, 2, 14, 15, 0, tzinfo=UTC),
        ),
    )
    assert invalid.applied is False
    assert "Некорректный" in invalid.message

    first = service.upsert_day_off(
        master_telegram_user_id=1000001,
        command=MasterDayOffCommand(
            start_at=datetime(2026, 2, 14, 15, 0, tzinfo=UTC),
            end_at=datetime(2026, 2, 14, 17, 0, tzinfo=UTC),
        ),
    )
    assert first.applied is True
    assert first.block_id is not None

    overlap = service.upsert_day_off(
        master_telegram_user_id=1000001,
        command=MasterDayOffCommand(
            start_at=datetime(2026, 2, 14, 16, 0, tzinfo=UTC),
            end_at=datetime(2026, 2, 14, 18, 0, tzinfo=UTC),
        ),
    )
    assert overlap.applied is False
    assert "пересекается" in overlap.message

    non_owner_update = service.upsert_day_off(
        master_telegram_user_id=1000002,
        command=MasterDayOffCommand(
            block_id=first.block_id,
            start_at=datetime(2026, 2, 14, 18, 0, tzinfo=UTC),
            end_at=datetime(2026, 2, 14, 19, 0, tzinfo=UTC),
        ),
    )
    assert non_owner_update.applied is False
    assert "не найден" in non_owner_update.message.lower()


def test_telegram_booking_flow_start_and_select_steps() -> None:
    engine = _setup_telegram_flow_schema()
    flow = TelegramBookingFlowService(engine)

    start_payload = flow.start()
    assert start_payload["message"] == "Выберите мастера."
    masters = start_payload["masters"]
    assert isinstance(masters, list)
    assert len(masters) == 2

    select_master_payload = flow.select_master(1)
    assert select_master_payload["message"] == "Выберите услугу."
    service_options = select_master_payload["service_options"]
    assert isinstance(service_options, list)
    assert len(service_options) == 3

    select_service_payload = flow.select_service(master_id=1, on_date=date(2026, 2, 12))
    assert select_service_payload["message"] == "Выберите доступный слот."
    slots = select_service_payload["slots"]
    assert isinstance(slots, list)
    assert len(slots) > 0


def test_telegram_booking_flow_confirm_sends_notifications_and_rejects_second_future_booking() -> None:
    engine = _setup_telegram_flow_schema()
    flow = TelegramBookingFlowService(engine)

    first = flow.confirm(
        client_telegram_user_id=2000001,
        master_id=1,
        service_type="haircut",
        slot_start=datetime(2026, 2, 12, 10, 0, tzinfo=UTC),
    )
    assert first["created"] is True
    notifications = first["notifications"]
    assert isinstance(notifications, list)
    assert len(notifications) == 2
    recipients = {item["recipient_telegram_user_id"] for item in notifications}
    assert recipients == {2000001, 1000001}

    second = flow.confirm(
        client_telegram_user_id=2000001,
        master_id=1,
        service_type="beard",
        slot_start=datetime(2026, 2, 12, 12, 0, tzinfo=UTC),
    )
    assert second["created"] is False
    assert "активная будущая" in str(second["message"])


def test_telegram_booking_flow_cancel_sends_notifications_and_rejects_non_owner() -> None:
    engine = _setup_telegram_flow_schema()
    flow = TelegramBookingFlowService(engine)

    created = flow.confirm(
        client_telegram_user_id=2000001,
        master_id=1,
        service_type="haircut",
        slot_start=datetime(2026, 2, 12, 10, 0, tzinfo=UTC),
    )
    booking_id = int(created["booking_id"])

    cancelled = flow.cancel(client_telegram_user_id=2000001, booking_id=booking_id)
    assert cancelled["cancelled"] is True
    notifications = cancelled["notifications"]
    assert isinstance(notifications, list)
    assert len(notifications) == 2
    recipients = {item["recipient_telegram_user_id"] for item in notifications}
    assert recipients == {2000001, 1000001}

    rejected = flow.cancel(client_telegram_user_id=2000002, booking_id=booking_id)
    assert rejected["cancelled"] is False


def test_telegram_master_cancel_sends_reason_to_client_and_rejects_without_reason() -> None:
    engine = _setup_telegram_flow_schema()
    flow = TelegramBookingFlowService(engine)

    created = flow.confirm(
        client_telegram_user_id=2000001,
        master_id=1,
        service_type="haircut",
        slot_start=datetime(2026, 2, 13, 10, 0, tzinfo=UTC),
    )
    booking_id = int(created["booking_id"])

    no_reason = flow.cancel_by_master(
        master_telegram_user_id=1000001,
        booking_id=booking_id,
        reason=" ",
    )
    assert no_reason["cancelled"] is False

    cancelled = flow.cancel_by_master(
        master_telegram_user_id=1000001,
        booking_id=booking_id,
        reason="Непредвиденные обстоятельства",
    )
    assert cancelled["cancelled"] is True
    notifications = cancelled["notifications"]
    assert isinstance(notifications, list)
    assert len(notifications) == 2
    recipients = {item["recipient_telegram_user_id"] for item in notifications}
    assert recipients == {2000001, 1000001}
    client_message = next(
        item["message"] for item in notifications if item["recipient_telegram_user_id"] == 2000001
    )
    assert "Непредвиденные обстоятельства" in client_message
