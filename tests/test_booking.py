from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.booking.availability import AvailabilityService
from app.booking.create_booking import BookingService
from app.booking.service_options import (
    SERVICE_OPTION_CODES,
    SERVICE_OPTION_LABELS_RU,
    list_service_options,
)


def _setup_availability_schema() -> Engine:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE masters (
                    id INTEGER PRIMARY KEY,
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
                    slot_start TEXT NOT NULL,
                    slot_end TEXT NOT NULL
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
                    start_at TEXT NOT NULL,
                    end_at TEXT NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT INTO masters (id, is_active, work_start, work_end, lunch_start, lunch_end)
                VALUES (1, 1, '10:00:00', '21:00:00', '13:00:00', '14:00:00')
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
                VALUES (1, 'active', '2026-02-09T11:00:00+00:00', '2026-02-09T12:00:00+00:00')
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO availability_blocks (master_id, start_at, end_at)
                VALUES
                    (1, '2026-02-09T15:00:00+00:00', '2026-02-09T16:00:00+00:00'),
                    (1, '2026-02-09T18:00:00+00:00', '2026-02-09T20:00:00+00:00')
                """
            )
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
                    (1, '2026-02-10T14:00:00+00:00', '2026-02-10T15:00:00+00:00'),
                    (1, '2026-02-10T16:00:00+00:00', '2026-02-10T17:00:00+00:00')
                """
            )
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
                VALUES (1, 9001, 'beard', 'active', '2026-02-11T10:00:00+00:00', '2026-02-11T11:00:00+00:00')
                """
            )
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
                VALUES (1, 5001, 'beard', 'active', '2026-02-11T12:00:00+00:00', '2026-02-11T13:00:00+00:00')
                """
            )
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
