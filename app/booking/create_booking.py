from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.booking.messages import RU_BOOKING_MESSAGES
from app.booking.service_options import SERVICE_OPTION_CODES

SLOT_DURATION = timedelta(minutes=60)
ACTIVE_STATUS = "active"


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
        if service_type not in SERVICE_OPTION_CODES:
            return BookingCreateResult(created=False, message=RU_BOOKING_MESSAGES["invalid_service_type"])

        slot_start_utc = _to_utc(slot_start)
        slot_end_utc = slot_start_utc + SLOT_DURATION
        now_utc = _to_utc(now) if now is not None else datetime.now(UTC)

        with self._engine.begin() as conn:
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

            day_work_start = slot_start_utc.replace(
                hour=work_start.hour,
                minute=work_start.minute,
                second=work_start.second,
                microsecond=0,
            )
            day_work_end = slot_start_utc.replace(
                hour=work_end.hour,
                minute=work_end.minute,
                second=work_end.second,
                microsecond=0,
            )
            day_lunch_start = slot_start_utc.replace(
                hour=lunch_start.hour,
                minute=lunch_start.minute,
                second=lunch_start.second,
                microsecond=0,
            )
            day_lunch_end = slot_start_utc.replace(
                hour=lunch_end.hour,
                minute=lunch_end.minute,
                second=lunch_end.second,
                microsecond=0,
            )

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
                    "status": ACTIVE_STATUS,
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
                    "status": ACTIVE_STATUS,
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
                    "status": ACTIVE_STATUS,
                },
            ).scalar_one()

            return BookingCreateResult(
                created=True,
                message=RU_BOOKING_MESSAGES["created"],
                booking_id=int(booking_id),
            )


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_time(value: time | str) -> time:
    if isinstance(value, time):
        return value
    return time.fromisoformat(value)
