from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.booking.contracts import BOOKING_STATUS_ACTIVE
from app.booking.guardrails import is_slot_start_allowed
from app.booking.messages import RU_BOOKING_MESSAGES
from app.booking.service_options import DEFAULT_SLOT_STEP_MINUTES, resolve_service_duration_minutes
from app.timezone import business_date, combine_business_date_time, normalize_utc, utc_now


@dataclass(frozen=True)
class BookingCreateResult:
    created: bool
    message: str
    booking_id: int | None = None


class BookingService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_booking(
        self,
        *,
        master_id: int,
        client_user_id: int,
        service_type: str,
        slot_start: datetime,
        now: datetime | None = None,
    ) -> BookingCreateResult:
        slot_start_utc = _to_utc(slot_start)
        now_utc = _to_utc(now) if now is not None else utc_now()

        with self._engine.begin() as conn:
            duration_minutes = resolve_service_duration_minutes(service_type, connection=conn)
            if duration_minutes is None:
                return BookingCreateResult(created=False, message=RU_BOOKING_MESSAGES["invalid_service_type"])

            slot_end_utc = slot_start_utc + timedelta(minutes=duration_minutes)

            master = conn.execute(
                text(
                    """
                    SELECT work_start, work_end, lunch_start, lunch_end
                    FROM masters
                    WHERE id = :master_id AND is_active = true
                    """
                ),
                {"master_id": master_id},
            ).mappings().first()
            if master is None:
                return BookingCreateResult(created=False, message=RU_BOOKING_MESSAGES["master_not_found"])

            work_start = _as_time(master["work_start"])
            work_end = _as_time(master["work_end"])
            lunch_start = _as_time(master["lunch_start"])
            lunch_end = _as_time(master["lunch_end"])

            business_slot_date = business_date(slot_start_utc)
            day_work_start = combine_business_date_time(business_slot_date, work_start)
            day_work_end = combine_business_date_time(business_slot_date, work_end)
            day_lunch_start = combine_business_date_time(business_slot_date, lunch_start)
            day_lunch_end = combine_business_date_time(business_slot_date, lunch_end)

            if not is_slot_start_allowed(
                slot_start=slot_start_utc,
                now=now_utc,
                slot_step_minutes=DEFAULT_SLOT_STEP_MINUTES,
            ):
                return BookingCreateResult(created=False, message=RU_BOOKING_MESSAGES["slot_already_passed"])

            if slot_start_utc < day_work_start or slot_end_utc > day_work_end:
                return BookingCreateResult(created=False, message=RU_BOOKING_MESSAGES["slot_not_available"])

            if slot_start_utc < day_lunch_end and day_lunch_start < slot_end_utc:
                return BookingCreateResult(created=False, message=RU_BOOKING_MESSAGES["slot_not_available"])

            existing_future = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM bookings
                    WHERE client_user_id = :client_user_id
                      AND status = :status
                      AND slot_start > :now_at
                    LIMIT 1
                    """
                ),
                {
                    "client_user_id": client_user_id,
                    "status": BOOKING_STATUS_ACTIVE,
                    "now_at": now_utc,
                },
            ).first()
            if existing_future is not None:
                return BookingCreateResult(created=False, message=RU_BOOKING_MESSAGES["client_future_booking_exists"])

            overlaps = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM bookings
                    WHERE master_id = :master_id
                      AND status = :status
                      AND slot_start < :slot_end
                      AND :slot_start < slot_end
                    LIMIT 1
                    """
                ),
                {
                    "master_id": master_id,
                    "status": BOOKING_STATUS_ACTIVE,
                    "slot_start": slot_start_utc,
                    "slot_end": slot_end_utc,
                },
            ).first()
            if overlaps is not None:
                return BookingCreateResult(created=False, message=RU_BOOKING_MESSAGES["slot_not_available"])

            blocked = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM availability_blocks
                    WHERE master_id = :master_id
                      AND start_at < :slot_end
                      AND :slot_start < end_at
                    LIMIT 1
                    """
                ),
                {
                    "master_id": master_id,
                    "slot_start": slot_start_utc,
                    "slot_end": slot_end_utc,
                },
            ).first()
            if blocked is not None:
                return BookingCreateResult(created=False, message=RU_BOOKING_MESSAGES["slot_not_available"])

            booking_id = conn.execute(
                text(
                    """
                    INSERT INTO bookings (master_id, client_user_id, service_type, slot_start, slot_end, status)
                    VALUES (:master_id, :client_user_id, :service_type, :slot_start, :slot_end, :status)
                    RETURNING id
                    """
                ),
                {
                    "master_id": master_id,
                    "client_user_id": client_user_id,
                    "service_type": service_type,
                    "slot_start": slot_start_utc,
                    "slot_end": slot_end_utc,
                    "status": BOOKING_STATUS_ACTIVE,
                },
            ).scalar_one()

            return BookingCreateResult(
                created=True,
                message=RU_BOOKING_MESSAGES["created"],
                booking_id=int(booking_id),
            )


def _to_utc(value: datetime) -> datetime:
    return normalize_utc(value)


def _as_time(value: time | str) -> time:
    if isinstance(value, time):
        return value
    return time.fromisoformat(value)
