from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.booking.availability import AvailabilityService
from app.booking.cancel_booking import BookingCancellationService
from app.booking.create_booking import BookingService
from app.booking.messages import RU_BOOKING_MESSAGES
from app.booking.service_options import SERVICE_OPTION_LABELS_RU, list_service_options
from app.timezone import normalize_utc, to_business, utc_now


@dataclass(frozen=True)
class BookingNotification:
    recipient_telegram_user_id: int
    message: str


class BookingFlowRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_active_masters(self) -> list[dict[str, int | str]]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT m.id, m.display_name, u.telegram_user_id
                    FROM masters m
                    JOIN users u ON u.id = m.user_id
                    WHERE m.is_active = true
                    ORDER BY m.id
                    """
                )
            ).mappings()
            return [
                {
                    "id": int(row["id"]),
                    "display_name": str(row["display_name"]),
                    "telegram_user_id": int(row["telegram_user_id"]),
                }
                for row in rows
            ]

    def resolve_client_user_id(self, telegram_user_id: int) -> int | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT u.id
                    FROM users u
                    JOIN roles r ON r.id = u.role_id
                    WHERE u.telegram_user_id = :telegram_user_id
                      AND r.name = 'Client'
                    """
                ),
                {"telegram_user_id": telegram_user_id},
            ).first()
            return int(row[0]) if row else None

    def resolve_master_user_id(self, telegram_user_id: int) -> int | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT u.id
                    FROM users u
                    JOIN roles r ON r.id = u.role_id
                    WHERE u.telegram_user_id = :telegram_user_id
                      AND r.name = 'Master'
                    """
                ),
                {"telegram_user_id": telegram_user_id},
            ).first()
            return int(row[0]) if row else None

    def get_master_telegram_user_id(self, master_id: int) -> int | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT u.telegram_user_id
                    FROM masters m
                    JOIN users u ON u.id = m.user_id
                    WHERE m.id = :master_id
                    """
                ),
                {"master_id": master_id},
            ).first()
            return int(row[0]) if row else None

    def get_client_telegram_user_id(self, client_user_id: int) -> int | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT telegram_user_id
                    FROM users
                    WHERE id = :client_user_id
                    """
                ),
                {"client_user_id": client_user_id},
            ).first()
            return int(row[0]) if row else None

    def get_booking_notification_context(self, booking_id: int) -> dict[str, object] | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT
                        b.slot_start,
                        b.service_type,
                        b.manual_client_name,
                        COALESCE(b.client_username_snapshot, u.telegram_username) AS client_username,
                        COALESCE(b.client_phone_snapshot, u.phone_number) AS client_phone
                    FROM bookings b
                    LEFT JOIN users u ON u.id = b.client_user_id
                    WHERE b.id = :booking_id
                    """
                ),
                {"booking_id": booking_id},
            ).mappings().first()
            if row is None:
                return None
            return {
                "slot_start": row["slot_start"],
                "service_type": row["service_type"],
                "manual_client_name": row["manual_client_name"],
                "client_username": row["client_username"],
                "client_phone": row["client_phone"],
            }


class BookingNotificationService:
    def build_booking_confirmation(
        self,
        *,
        client_telegram_user_id: int,
        master_telegram_user_id: int,
        slot_start: datetime | None,
        service_type: str | None,
        manual_client_name: str | None = None,
        client_username: str | None = None,
        client_phone: str | None = None,
    ) -> list[BookingNotification]:
        slot_text = _format_slot_datetime(slot_start)
        service_label = _resolve_service_label(service_type)
        client_text = _build_client_identity_text(
            manual_client_name=manual_client_name,
            client_username=client_username,
            client_phone=client_phone,
            fallback_client_telegram_user_id=client_telegram_user_id,
        )
        return [
            BookingNotification(
                recipient_telegram_user_id=client_telegram_user_id,
                message=RU_BOOKING_MESSAGES["booking_confirmed_client"],
            ),
            BookingNotification(
                recipient_telegram_user_id=master_telegram_user_id,
                message=(
                    f"{RU_BOOKING_MESSAGES['booking_confirmed_master']}\n"
                    f"{client_text}\n"
                    f"Слот: {slot_text}\n"
                    f"Услуга: {service_label}"
                ).strip(),
            ),
        ]

    def build_client_cancellation(
        self,
        *,
        client_telegram_user_id: int,
        master_telegram_user_id: int,
    ) -> list[BookingNotification]:
        return [
            BookingNotification(
                recipient_telegram_user_id=client_telegram_user_id,
                message=RU_BOOKING_MESSAGES["booking_cancelled_client"],
            ),
            BookingNotification(
                recipient_telegram_user_id=master_telegram_user_id,
                message=RU_BOOKING_MESSAGES["booking_cancelled_master"],
            ),
        ]

    def build_master_cancellation(
        self,
        *,
        client_telegram_user_id: int,
        master_telegram_user_id: int,
        reason: str,
        slot_start: datetime | None,
    ) -> list[BookingNotification]:
        slot_text = _format_slot_datetime(slot_start)
        return [
            BookingNotification(
                recipient_telegram_user_id=client_telegram_user_id,
                message=(
                    f"{RU_BOOKING_MESSAGES['booking_cancelled_by_master_client_prefix'].format(reason=reason)}\n"
                    f"Слот: {slot_text}"
                ),
            ),
            BookingNotification(
                recipient_telegram_user_id=master_telegram_user_id,
                message=RU_BOOKING_MESSAGES["booking_cancelled_by_master_master"],
            ),
        ]


class TelegramBookingFlowService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._repository = BookingFlowRepository(engine)
        self._availability = AvailabilityService(engine)
        self._bookings = BookingService(engine)
        self._cancellations = BookingCancellationService(engine)
        self._notifications = BookingNotificationService()

    def start(self) -> dict[str, object]:
        masters = self._repository.list_active_masters()
        return {
            "message": RU_BOOKING_MESSAGES["choose_master"],
            "masters": masters,
        }

    def select_master(self, master_id: int) -> dict[str, object]:
        if not any(master["id"] == master_id for master in self._repository.list_active_masters()):
            return {"message": RU_BOOKING_MESSAGES["master_not_found"], "service_options": []}

        return {
            "message": RU_BOOKING_MESSAGES["choose_service"],
            "service_options": list_service_options(),
        }

    def select_service(self, *, master_id: int, on_date: date, service_type: str) -> dict[str, object]:
        if not any(master["id"] == master_id for master in self._repository.list_active_masters()):
            return {"message": RU_BOOKING_MESSAGES["master_not_found"], "slots": []}

        slots = self._availability.list_slots(
            master_id=master_id,
            on_date=on_date,
            service_type=service_type,
            now=utc_now(),
        )
        return {
            "message": RU_BOOKING_MESSAGES["choose_slot"],
            "slots": [
                {"start_at": slot.start_at.isoformat(), "end_at": slot.end_at.isoformat()}
                for slot in slots
            ],
        }

    def confirm(
        self,
        *,
        client_telegram_user_id: int,
        master_id: int,
        service_type: str,
        slot_start: datetime,
    ) -> dict[str, object]:
        client_user_id = self._repository.resolve_client_user_id(client_telegram_user_id)
        if client_user_id is None:
            return {
                "created": False,
                "booking_id": None,
                "message": RU_BOOKING_MESSAGES["client_not_found"],
                "notifications": [],
            }

        result = self._bookings.create_booking(
            master_id=master_id,
            client_user_id=client_user_id,
            service_type=service_type,
            slot_start=slot_start,
        )

        if not result.created:
            return {
                "created": False,
                "booking_id": None,
                "message": result.message,
                "notifications": [],
            }

        result_context = (
            self._repository.get_booking_notification_context(result.booking_id)
            if result.booking_id is not None
            else None
        )
        master_telegram_user_id = self._repository.get_master_telegram_user_id(master_id)
        notifications = (
            self._notifications.build_booking_confirmation(
                client_telegram_user_id=client_telegram_user_id,
                master_telegram_user_id=master_telegram_user_id,
                slot_start=_as_datetime_or_none(result_context.get("slot_start") if result_context else None),
                service_type=_as_str_or_none(result_context.get("service_type") if result_context else None),
                manual_client_name=_as_str_or_none(result_context.get("manual_client_name") if result_context else None),
                client_username=_as_str_or_none(result_context.get("client_username") if result_context else None),
                client_phone=_as_str_or_none(result_context.get("client_phone") if result_context else None),
            )
            if master_telegram_user_id is not None
            else []
        )

        return {
            "created": True,
            "booking_id": result.booking_id,
            "message": result.message,
            "notifications": [
                {
                    "recipient_telegram_user_id": n.recipient_telegram_user_id,
                    "message": n.message,
                }
                for n in notifications
            ],
        }

    def cancel(
        self,
        *,
        client_telegram_user_id: int,
        booking_id: int,
    ) -> dict[str, object]:
        client_user_id = self._repository.resolve_client_user_id(client_telegram_user_id)
        if client_user_id is None:
            return {
                "cancelled": False,
                "booking_id": None,
                "message": RU_BOOKING_MESSAGES["client_not_found"],
                "notifications": [],
            }

        result = self._cancellations.cancel_by_client(booking_id=booking_id, client_user_id=client_user_id)
        if not result.cancelled:
            return {
                "cancelled": False,
                "booking_id": None,
                "message": result.message,
                "notifications": [],
            }

        notifications: list[BookingNotification] = [
            BookingNotification(
                recipient_telegram_user_id=client_telegram_user_id,
                message=RU_BOOKING_MESSAGES["booking_cancelled_client"],
            )
        ]
        if result.master_id is not None:
            master_telegram_user_id = self._repository.get_master_telegram_user_id(result.master_id)
            if master_telegram_user_id is not None:
                notifications = self._notifications.build_client_cancellation(
                    client_telegram_user_id=client_telegram_user_id,
                    master_telegram_user_id=master_telegram_user_id,
                )

        return {
            "cancelled": True,
            "booking_id": result.booking_id,
            "message": result.message,
            "notifications": [
                {
                    "recipient_telegram_user_id": n.recipient_telegram_user_id,
                    "message": n.message,
                }
                for n in notifications
            ],
        }

    def cancel_by_master(
        self,
        *,
        master_telegram_user_id: int,
        booking_id: int,
        reason: str,
    ) -> dict[str, object]:
        master_user_id = self._repository.resolve_master_user_id(master_telegram_user_id)
        if master_user_id is None:
            return {
                "cancelled": False,
                "booking_id": None,
                "message": RU_BOOKING_MESSAGES["master_not_found"],
                "notifications": [],
            }

        result = self._cancellations.cancel_by_master(
            booking_id=booking_id,
            master_user_id=master_user_id,
            reason=reason,
        )
        if not result.cancelled:
            return {
                "cancelled": False,
                "booking_id": None,
                "message": result.message,
                "notifications": [],
            }

        notifications: list[BookingNotification] = [
            BookingNotification(
                recipient_telegram_user_id=master_telegram_user_id,
                message=RU_BOOKING_MESSAGES["booking_cancelled_by_master_master"],
            )
        ]
        if result.client_user_id is not None and result.cancellation_reason is not None:
            client_telegram_user_id = self._repository.get_client_telegram_user_id(result.client_user_id)
            if client_telegram_user_id is not None:
                notifications = self._notifications.build_master_cancellation(
                    client_telegram_user_id=client_telegram_user_id,
                    master_telegram_user_id=master_telegram_user_id,
                    reason=result.cancellation_reason,
                    slot_start=result.slot_start,
                )

        return {
            "cancelled": True,
            "booking_id": result.booking_id,
            "message": result.message,
            "notifications": [
                {
                    "recipient_telegram_user_id": n.recipient_telegram_user_id,
                    "message": n.message,
                }
                for n in notifications
            ],
        }


def _build_client_identity_text(
    *,
    manual_client_name: str | None,
    client_username: str | None,
    client_phone: str | None,
    fallback_client_telegram_user_id: int,
) -> str:
    if manual_client_name and manual_client_name.strip():
        base = f"Клиент: {manual_client_name.strip()}"
    elif client_username and client_username.strip():
        normalized = client_username.strip().lstrip("@")
        base = f"Клиент: @{normalized}"
    else:
        base = f"Клиент: ID {fallback_client_telegram_user_id}"
    if client_phone and client_phone.strip():
        base = f"{base}\nТелефон: {client_phone.strip()}"
    return base


def _format_slot_datetime(value: datetime | None) -> str:
    if value is None:
        return "не указан"
    return to_business(normalize_utc(value)).strftime("%d.%m.%Y %H:%M")


def _resolve_service_label(service_type: str | None) -> str:
    if service_type is None:
        return "не указана"
    return SERVICE_OPTION_LABELS_RU.get(service_type, service_type)


def _as_datetime_or_none(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return normalize_utc(value)
    if isinstance(value, str):
        return normalize_utc(datetime.fromisoformat(value))
    return None


def _as_str_or_none(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None
