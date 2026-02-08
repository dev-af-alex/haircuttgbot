from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.booking.contracts import (
    BOOKING_STATUS_CANCELLED_BY_CLIENT,
    BOOKING_STATUS_CANCELLED_BY_MASTER,
    can_transition_booking_status,
    is_cancellation_reason_required,
)
from app.booking.messages import RU_BOOKING_MESSAGES


@dataclass(frozen=True)
class BookingCancelResult:
    cancelled: bool
    message: str
    booking_id: int | None = None
    master_id: int | None = None
    client_user_id: int | None = None
    cancellation_reason: str | None = None


class BookingCancellationService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def cancel_by_client(
        self,
        *,
        booking_id: int,
        client_user_id: int,
        now: datetime | None = None,
    ) -> BookingCancelResult:
        now_utc = _to_utc(now) if now is not None else datetime.now(UTC)

        with self._engine.begin() as conn:
            booking = conn.execute(
                text(
                    """
                    SELECT id, master_id, status, slot_start
                    FROM bookings
                    WHERE id = :booking_id
                      AND client_user_id = :client_user_id
                    """
                ),
                {
                    "booking_id": booking_id,
                    "client_user_id": client_user_id,
                },
            ).mappings().first()
            if booking is None:
                return BookingCancelResult(cancelled=False, message=RU_BOOKING_MESSAGES["cancel_not_allowed"])

            current_status = str(booking["status"])
            slot_start = _coerce_datetime(booking["slot_start"])

            if slot_start <= now_utc:
                return BookingCancelResult(cancelled=False, message=RU_BOOKING_MESSAGES["cancel_not_allowed"])

            if not can_transition_booking_status(
                current_status=current_status,
                target_status=BOOKING_STATUS_CANCELLED_BY_CLIENT,
            ):
                return BookingCancelResult(cancelled=False, message=RU_BOOKING_MESSAGES["cancel_not_allowed"])

            updated = conn.execute(
                text(
                    """
                    UPDATE bookings
                    SET status = :target_status,
                        cancellation_reason = NULL
                    WHERE id = :booking_id
                      AND status = :current_status
                    """
                ),
                {
                    "booking_id": int(booking["id"]),
                    "target_status": BOOKING_STATUS_CANCELLED_BY_CLIENT,
                    "current_status": current_status,
                },
            )
            if updated.rowcount != 1:
                return BookingCancelResult(cancelled=False, message=RU_BOOKING_MESSAGES["cancel_not_allowed"])

            return BookingCancelResult(
                cancelled=True,
                message=RU_BOOKING_MESSAGES["cancelled"],
                booking_id=int(booking["id"]),
                master_id=int(booking["master_id"]),
                client_user_id=client_user_id,
            )

    def cancel_by_master(
        self,
        *,
        booking_id: int,
        master_user_id: int,
        reason: str,
        now: datetime | None = None,
    ) -> BookingCancelResult:
        now_utc = _to_utc(now) if now is not None else datetime.now(UTC)
        normalized_reason = reason.strip()

        if is_cancellation_reason_required(target_status=BOOKING_STATUS_CANCELLED_BY_MASTER) and not normalized_reason:
            return BookingCancelResult(cancelled=False, message=RU_BOOKING_MESSAGES["cancel_reason_required"])

        with self._engine.begin() as conn:
            booking = conn.execute(
                text(
                    """
                    SELECT b.id, b.master_id, b.client_user_id, b.status, b.slot_start
                    FROM bookings b
                    JOIN masters m ON m.id = b.master_id
                    WHERE b.id = :booking_id
                      AND m.user_id = :master_user_id
                    """
                ),
                {
                    "booking_id": booking_id,
                    "master_user_id": master_user_id,
                },
            ).mappings().first()
            if booking is None:
                return BookingCancelResult(cancelled=False, message=RU_BOOKING_MESSAGES["cancel_not_allowed"])

            current_status = str(booking["status"])
            slot_start = _coerce_datetime(booking["slot_start"])

            if slot_start <= now_utc:
                return BookingCancelResult(cancelled=False, message=RU_BOOKING_MESSAGES["cancel_not_allowed"])

            if not can_transition_booking_status(
                current_status=current_status,
                target_status=BOOKING_STATUS_CANCELLED_BY_MASTER,
            ):
                return BookingCancelResult(cancelled=False, message=RU_BOOKING_MESSAGES["cancel_not_allowed"])

            updated = conn.execute(
                text(
                    """
                    UPDATE bookings
                    SET status = :target_status,
                        cancellation_reason = :cancellation_reason
                    WHERE id = :booking_id
                      AND status = :current_status
                    """
                ),
                {
                    "booking_id": int(booking["id"]),
                    "target_status": BOOKING_STATUS_CANCELLED_BY_MASTER,
                    "cancellation_reason": normalized_reason,
                    "current_status": current_status,
                },
            )
            if updated.rowcount != 1:
                return BookingCancelResult(cancelled=False, message=RU_BOOKING_MESSAGES["cancel_not_allowed"])

            return BookingCancelResult(
                cancelled=True,
                message=RU_BOOKING_MESSAGES["cancelled"],
                booking_id=int(booking["id"]),
                master_id=int(booking["master_id"]),
                client_user_id=int(booking["client_user_id"]),
                cancellation_reason=normalized_reason,
            )


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _coerce_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return _to_utc(value)
    return _to_utc(datetime.fromisoformat(value))
