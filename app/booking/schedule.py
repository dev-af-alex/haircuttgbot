from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from app.booking.contracts import BOOKING_STATUS_ACTIVE
from app.booking.messages import RU_BOOKING_MESSAGES
from app.booking.service_options import resolve_service_duration_minutes

BLOCK_TYPE_DAY_OFF = "day_off"


@dataclass(frozen=True)
class MasterScheduleContext:
    master_user_id: int
    master_id: int


@dataclass(frozen=True)
class MasterDayOffCommand:
    start_at: datetime
    end_at: datetime
    block_id: int | None = None


@dataclass(frozen=True)
class MasterLunchBreakCommand:
    lunch_start: time
    lunch_end: time


@dataclass(frozen=True)
class MasterManualBookingCommand:
    client_name: str
    service_type: str
    slot_start: datetime


@dataclass(frozen=True)
class MasterDayOffResult:
    applied: bool
    created: bool
    block_id: int | None
    message: str


@dataclass(frozen=True)
class MasterLunchBreakResult:
    applied: bool
    message: str


@dataclass(frozen=True)
class MasterManualBookingResult:
    applied: bool
    booking_id: int | None
    message: str


class MasterScheduleService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def resolve_context(self, *, master_telegram_user_id: int) -> MasterScheduleContext | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT u.id AS master_user_id, m.id AS master_id
                    FROM users u
                    JOIN roles r ON r.id = u.role_id
                    JOIN masters m ON m.user_id = u.id
                    WHERE u.telegram_user_id = :master_telegram_user_id
                      AND r.name = 'Master'
                      AND m.is_active = true
                    """
                ),
                {"master_telegram_user_id": master_telegram_user_id},
            ).mappings().first()
            if row is None:
                return None
            return MasterScheduleContext(
                master_user_id=int(row["master_user_id"]),
                master_id=int(row["master_id"]),
            )

    def upsert_day_off(
        self,
        *,
        master_telegram_user_id: int,
        command: MasterDayOffCommand,
    ) -> MasterDayOffResult:
        start_at = _to_utc(command.start_at)
        end_at = _to_utc(command.end_at)
        if start_at >= end_at:
            return MasterDayOffResult(
                applied=False,
                created=False,
                block_id=None,
                message=RU_BOOKING_MESSAGES["day_off_invalid_interval"],
            )

        context = self.resolve_context(master_telegram_user_id=master_telegram_user_id)
        if context is None:
            return MasterDayOffResult(
                applied=False,
                created=False,
                block_id=None,
                message=RU_BOOKING_MESSAGES["master_not_found"],
            )

        with self._engine.begin() as conn:
            if self._has_active_booking_overlap(
                conn=conn,
                master_id=context.master_id,
                start_at=start_at,
                end_at=end_at,
            ):
                return MasterDayOffResult(
                    applied=False,
                    created=False,
                    block_id=None,
                    message=RU_BOOKING_MESSAGES["day_off_has_bookings"],
                )

            overlapping = conn.execute(
                text(
                    """
                    SELECT id
                    FROM availability_blocks
                    WHERE master_id = :master_id
                      AND block_type = :block_type
                      AND start_at < :end_at
                      AND :start_at < end_at
                      AND (:block_id IS NULL OR id <> :block_id)
                    LIMIT 1
                    """
                ),
                {
                    "master_id": context.master_id,
                    "block_type": BLOCK_TYPE_DAY_OFF,
                    "start_at": start_at,
                    "end_at": end_at,
                    "block_id": command.block_id,
                },
            ).first()
            if overlapping is not None:
                return MasterDayOffResult(
                    applied=False,
                    created=False,
                    block_id=None,
                    message=RU_BOOKING_MESSAGES["day_off_conflict"],
                )

            if command.block_id is not None:
                updated = conn.execute(
                    text(
                        """
                        UPDATE availability_blocks
                        SET start_at = :start_at,
                            end_at = :end_at,
                            reason = :reason
                        WHERE id = :block_id
                          AND master_id = :master_id
                          AND block_type = :block_type
                        """
                    ),
                    {
                        "block_id": command.block_id,
                        "master_id": context.master_id,
                        "block_type": BLOCK_TYPE_DAY_OFF,
                        "start_at": start_at,
                        "end_at": end_at,
                        "reason": RU_BOOKING_MESSAGES["day_off_reason_default"],
                    },
                )
                if updated.rowcount != 1:
                    return MasterDayOffResult(
                        applied=False,
                        created=False,
                        block_id=None,
                        message=RU_BOOKING_MESSAGES["day_off_not_found"],
                    )
                return MasterDayOffResult(
                    applied=True,
                    created=False,
                    block_id=command.block_id,
                    message=RU_BOOKING_MESSAGES["day_off_updated"],
                )

            created_id = conn.execute(
                text(
                    """
                    INSERT INTO availability_blocks (master_id, block_type, start_at, end_at, reason)
                    VALUES (:master_id, :block_type, :start_at, :end_at, :reason)
                    RETURNING id
                    """
                ),
                {
                    "master_id": context.master_id,
                    "block_type": BLOCK_TYPE_DAY_OFF,
                    "start_at": start_at,
                    "end_at": end_at,
                    "reason": RU_BOOKING_MESSAGES["day_off_reason_default"],
                },
            ).scalar_one()
            return MasterDayOffResult(
                applied=True,
                created=True,
                block_id=int(created_id),
                message=RU_BOOKING_MESSAGES["day_off_created"],
            )

    def _has_active_booking_overlap(
        self,
        *,
        conn: Connection,
        master_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> bool:
        row = conn.execute(
            text(
                """
                SELECT 1
                FROM bookings
                WHERE master_id = :master_id
                  AND status = :active_status
                  AND slot_start < :end_at
                  AND :start_at < slot_end
                LIMIT 1
                """
            ),
            {
                "master_id": master_id,
                "active_status": BOOKING_STATUS_ACTIVE,
                "start_at": start_at,
                "end_at": end_at,
            },
        ).first()
        return row is not None

    def update_lunch_break(
        self,
        *,
        master_telegram_user_id: int,
        command: MasterLunchBreakCommand,
    ) -> MasterLunchBreakResult:
        lunch_start = command.lunch_start
        lunch_end = command.lunch_end
        if lunch_start >= lunch_end:
            return MasterLunchBreakResult(
                applied=False,
                message=RU_BOOKING_MESSAGES["lunch_invalid_interval"],
            )

        minutes = (lunch_end.hour * 60 + lunch_end.minute) - (lunch_start.hour * 60 + lunch_start.minute)
        if minutes != 60:
            return MasterLunchBreakResult(
                applied=False,
                message=RU_BOOKING_MESSAGES["lunch_invalid_duration"],
            )

        context = self.resolve_context(master_telegram_user_id=master_telegram_user_id)
        if context is None:
            return MasterLunchBreakResult(
                applied=False,
                message=RU_BOOKING_MESSAGES["master_not_found"],
            )

        with self._engine.begin() as conn:
            master = conn.execute(
                text(
                    """
                    SELECT work_start, work_end
                    FROM masters
                    WHERE id = :master_id
                    """
                ),
                {"master_id": context.master_id},
            ).mappings().first()
            if master is None:
                return MasterLunchBreakResult(
                    applied=False,
                    message=RU_BOOKING_MESSAGES["master_not_found"],
                )

            work_start = _as_time(master["work_start"])
            work_end = _as_time(master["work_end"])
            if lunch_start < work_start or lunch_end > work_end:
                return MasterLunchBreakResult(
                    applied=False,
                    message=RU_BOOKING_MESSAGES["lunch_outside_work_hours"],
                )

            updated = conn.execute(
                text(
                    """
                    UPDATE masters
                    SET lunch_start = :lunch_start,
                        lunch_end = :lunch_end
                    WHERE id = :master_id
                    """
                ),
                {
                    "master_id": context.master_id,
                    "lunch_start": lunch_start.isoformat(),
                    "lunch_end": lunch_end.isoformat(),
                },
            )
            if updated.rowcount != 1:
                return MasterLunchBreakResult(
                    applied=False,
                    message=RU_BOOKING_MESSAGES["master_not_found"],
                )
            return MasterLunchBreakResult(
                applied=True,
                message=RU_BOOKING_MESSAGES["lunch_updated"],
            )

    def create_manual_booking(
        self,
        *,
        master_telegram_user_id: int,
        command: MasterManualBookingCommand,
    ) -> MasterManualBookingResult:
        context = self.resolve_context(master_telegram_user_id=master_telegram_user_id)
        if context is None:
            return MasterManualBookingResult(
                applied=False,
                booking_id=None,
                message=RU_BOOKING_MESSAGES["master_not_found"],
            )

        slot_start = _to_utc(command.slot_start)

        with self._engine.begin() as conn:
            duration_minutes = resolve_service_duration_minutes(command.service_type, connection=conn)
            if duration_minutes is None:
                return MasterManualBookingResult(
                    applied=False,
                    booking_id=None,
                    message=RU_BOOKING_MESSAGES["invalid_service_type"],
                )

            slot_end = slot_start + timedelta(minutes=duration_minutes)

            master = conn.execute(
                text(
                    """
                    SELECT work_start, work_end, lunch_start, lunch_end
                    FROM masters
                    WHERE id = :master_id
                    """
                ),
                {"master_id": context.master_id},
            ).mappings().first()
            if master is None:
                return MasterManualBookingResult(
                    applied=False,
                    booking_id=None,
                    message=RU_BOOKING_MESSAGES["master_not_found"],
                )

            work_start = _as_time(master["work_start"])
            work_end = _as_time(master["work_end"])
            lunch_start = _as_time(master["lunch_start"])
            lunch_end = _as_time(master["lunch_end"])

            day_work_start = slot_start.replace(
                hour=work_start.hour,
                minute=work_start.minute,
                second=work_start.second,
                microsecond=0,
            )
            day_work_end = slot_start.replace(
                hour=work_end.hour,
                minute=work_end.minute,
                second=work_end.second,
                microsecond=0,
            )
            day_lunch_start = slot_start.replace(
                hour=lunch_start.hour,
                minute=lunch_start.minute,
                second=lunch_start.second,
                microsecond=0,
            )
            day_lunch_end = slot_start.replace(
                hour=lunch_end.hour,
                minute=lunch_end.minute,
                second=lunch_end.second,
                microsecond=0,
            )

            if slot_start < day_work_start or slot_end > day_work_end:
                return MasterManualBookingResult(
                    applied=False,
                    booking_id=None,
                    message=RU_BOOKING_MESSAGES["slot_not_available"],
                )

            if slot_start < day_lunch_end and day_lunch_start < slot_end:
                return MasterManualBookingResult(
                    applied=False,
                    booking_id=None,
                    message=RU_BOOKING_MESSAGES["slot_not_available"],
                )

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
                    "master_id": context.master_id,
                    "status": BOOKING_STATUS_ACTIVE,
                    "slot_start": slot_start,
                    "slot_end": slot_end,
                },
            ).first()
            if overlaps is not None:
                return MasterManualBookingResult(
                    applied=False,
                    booking_id=None,
                    message=RU_BOOKING_MESSAGES["manual_booking_conflict"],
                )

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
                    "master_id": context.master_id,
                    "slot_start": slot_start,
                    "slot_end": slot_end,
                },
            ).first()
            if blocked is not None:
                return MasterManualBookingResult(
                    applied=False,
                    booking_id=None,
                    message=RU_BOOKING_MESSAGES["manual_booking_conflict"],
                )

            # Manual bookings use a deterministic synthetic client user to satisfy
            # non-null client FK while preserving master ownership semantics.
            manual_client_tg = -(9_000_000_000 + context.master_id)
            conn.execute(
                text("INSERT INTO roles (name) VALUES ('Client') ON CONFLICT (name) DO NOTHING")
            )
            conn.execute(
                text(
                    """
                    INSERT INTO users (telegram_user_id, role_id)
                    VALUES (:telegram_user_id, (SELECT id FROM roles WHERE name='Client'))
                    ON CONFLICT (telegram_user_id) DO NOTHING
                    """
                ),
                {"telegram_user_id": manual_client_tg},
            )
            manual_client_user_id = conn.execute(
                text("SELECT id FROM users WHERE telegram_user_id = :telegram_user_id"),
                {"telegram_user_id": manual_client_tg},
            ).scalar_one()

            booking_id = conn.execute(
                text(
                    """
                    INSERT INTO bookings (master_id, client_user_id, service_type, slot_start, slot_end, status)
                    VALUES (:master_id, :client_user_id, :service_type, :slot_start, :slot_end, :status)
                    RETURNING id
                    """
                ),
                {
                    "master_id": context.master_id,
                    "client_user_id": int(manual_client_user_id),
                    "service_type": command.service_type,
                    "slot_start": slot_start,
                    "slot_end": slot_end,
                    "status": BOOKING_STATUS_ACTIVE,
                },
            ).scalar_one()
            return MasterManualBookingResult(
                applied=True,
                booking_id=int(booking_id),
                message=RU_BOOKING_MESSAGES["manual_booking_created"],
            )


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_time(value: time | str) -> time:
    if isinstance(value, time):
        return value
    return time.fromisoformat(value)
