from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Awaitable, Callable

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.booking.service_options import SERVICE_OPTION_LABELS_RU
from app.timezone import normalize_utc, to_business

REMINDER_STATUS_PENDING = "pending"
REMINDER_STATUS_SENT = "sent"
REMINDER_STATUS_SKIPPED = "skipped"
REMINDER_OUTCOME_SCHEDULED = "scheduled"
REMINDER_OUTCOME_SKIPPED = "skipped"
REMINDER_OUTCOME_REPLAYED = "replayed"
REMINDER_OUTCOME_FAILED = "failed"
REMINDER_LEAD_HOURS = 2


@dataclass(frozen=True)
class ReminderDispatchItem:
    reminder_id: int
    recipient_telegram_user_id: int
    message: str


class BookingReminderService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def schedule_for_booking(
        self,
        *,
        booking_id: int,
        slot_start: datetime,
        booking_created_at: datetime,
    ) -> str:
        slot_start_utc = normalize_utc(slot_start)
        created_at_utc = normalize_utc(booking_created_at)
        due_at_utc = slot_start_utc - timedelta(hours=REMINDER_LEAD_HOURS)
        status = (
            REMINDER_STATUS_PENDING
            if is_reminder_eligible(
                slot_start=slot_start_utc,
                booking_created_at=created_at_utc,
            )
            else REMINDER_STATUS_SKIPPED
        )
        try:
            with self._engine.begin() as conn:
                existing = conn.execute(
                    text(
                        """
                        SELECT status
                        FROM booking_reminders
                        WHERE booking_id = :booking_id
                        """
                    ),
                    {"booking_id": booking_id},
                ).first()
                if existing is not None:
                    return REMINDER_OUTCOME_REPLAYED

                conn.execute(
                    text(
                        """
                        INSERT INTO booking_reminders (booking_id, due_at, status)
                        VALUES (:booking_id, :due_at, :status)
                        """
                    ),
                    {
                        "booking_id": booking_id,
                        "due_at": due_at_utc,
                        "status": status,
                    },
                )
                return REMINDER_OUTCOME_SCHEDULED if status == REMINDER_STATUS_PENDING else REMINDER_OUTCOME_SKIPPED
        except Exception:
            return REMINDER_OUTCOME_FAILED

    async def dispatch_due_reminders(
        self,
        *,
        sender: Callable[[int, str], Awaitable[None]],
        now: datetime | None = None,
        limit: int = 50,
    ) -> dict[str, int]:
        now_utc = normalize_utc(now or datetime.now(UTC))
        outcomes = {"sent": 0, "failed": 0, "replayed": 0}
        due = self._claim_due(now=now_utc, limit=limit)
        for item in due:
            try:
                await sender(item.recipient_telegram_user_id, item.message)
                self._mark_sent(reminder_id=item.reminder_id, sent_at=now_utc)
                outcomes["sent"] += 1
            except Exception as exc:
                self._mark_failed(reminder_id=item.reminder_id, error=str(exc))
                outcomes["failed"] += 1
        return outcomes

    def _claim_due(self, *, now: datetime, limit: int) -> list[ReminderDispatchItem]:
        with self._engine.begin() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        br.id AS reminder_id,
                        u.telegram_user_id AS recipient_telegram_user_id,
                        b.slot_start,
                        b.service_type,
                        m.display_name
                    FROM booking_reminders br
                    JOIN bookings b ON b.id = br.booking_id
                    JOIN users u ON u.id = b.client_user_id
                    JOIN masters m ON m.id = b.master_id
                    WHERE br.status = :status_pending
                      AND br.due_at <= :now_at
                      AND b.status = 'active'
                      AND u.telegram_user_id > 0
                    ORDER BY br.due_at, br.id
                    LIMIT :limit
                    """
                ),
                {
                    "status_pending": REMINDER_STATUS_PENDING,
                    "now_at": now,
                    "limit": max(1, limit),
                },
            ).mappings()
            items: list[ReminderDispatchItem] = []
            for row in rows:
                reminder_id = int(row["reminder_id"])
                items.append(
                    ReminderDispatchItem(
                        reminder_id=reminder_id,
                        recipient_telegram_user_id=int(row["recipient_telegram_user_id"]),
                        message=_build_reminder_message(
                            slot_start=normalize_utc(_to_datetime(row["slot_start"])),
                            service_type=str(row["service_type"]),
                            master_display_name=str(row["display_name"]),
                        ),
                    )
                )
            return items

    def _mark_sent(self, *, reminder_id: int, sent_at: datetime) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE booking_reminders
                    SET status = :status,
                        sent_at = :sent_at,
                        last_error = NULL,
                        updated_at = :updated_at
                    WHERE id = :reminder_id
                    """
                ),
                {
                    "status": REMINDER_STATUS_SENT,
                    "sent_at": sent_at,
                    "updated_at": sent_at,
                    "reminder_id": reminder_id,
                },
            )

    def _mark_failed(self, *, reminder_id: int, error: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE booking_reminders
                    SET status = :status,
                        last_error = :error,
                        updated_at = :updated_at
                    WHERE id = :reminder_id
                    """
                ),
                {
                    "status": REMINDER_STATUS_PENDING,
                    "error": error[:500],
                    "updated_at": normalize_utc(datetime.now(UTC)),
                    "reminder_id": reminder_id,
                },
            )


def is_reminder_eligible(*, slot_start: datetime, booking_created_at: datetime) -> bool:
    slot_business = to_business(normalize_utc(slot_start))
    created_business = to_business(normalize_utc(booking_created_at))
    return (slot_business - created_business) >= timedelta(hours=REMINDER_LEAD_HOURS)


def _build_reminder_message(*, slot_start: datetime, service_type: str, master_display_name: str) -> str:
    slot_business = to_business(slot_start)
    service_label = SERVICE_OPTION_LABELS_RU.get(service_type, service_type)
    return (
        "Напоминание: у вас запись через 2 часа.\n"
        f"Мастер: {master_display_name}\n"
        f"Услуга: {service_label}\n"
        f"Слот: {slot_business.strftime('%d.%m.%Y %H:%M')}"
    )


def _to_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
