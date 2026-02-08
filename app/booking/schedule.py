from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.booking.messages import RU_BOOKING_MESSAGES

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


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
