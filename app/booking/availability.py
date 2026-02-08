from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Engine

SLOT_DURATION_MINUTES = 60
SLOT_DURATION = timedelta(minutes=SLOT_DURATION_MINUTES)


@dataclass(frozen=True)
class AvailabilitySlot:
    start_at: datetime
    end_at: datetime


class AvailabilityService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_slots(
        self,
        master_id: int,
        on_date: date,
        now: datetime | None = None,
    ) -> list[AvailabilitySlot]:
        """Return available [start, end) slots for a master/day."""
        with self._engine.connect() as conn:
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
                return []

            work_start = _as_time(master["work_start"])
            work_end = _as_time(master["work_end"])
            lunch_start = _as_time(master["lunch_start"])
            lunch_end = _as_time(master["lunch_end"])

            day_start = datetime.combine(on_date, time.min, tzinfo=UTC)
            day_end = day_start + timedelta(days=1)

            blocked_ranges = [
                (datetime.combine(on_date, lunch_start, tzinfo=UTC), datetime.combine(on_date, lunch_end, tzinfo=UTC))
            ]

            booking_rows = conn.execute(
                text(
                    """
                    SELECT slot_start, slot_end
                    FROM bookings
                    WHERE master_id = :master_id
                      AND status = 'active'
                      AND slot_end > :day_start
                      AND slot_start < :day_end
                    """
                ),
                {"master_id": master_id, "day_start": day_start, "day_end": day_end},
            ).mappings().all()

            block_rows = conn.execute(
                text(
                    """
                    SELECT start_at, end_at
                    FROM availability_blocks
                    WHERE master_id = :master_id
                      AND end_at > :day_start
                      AND start_at < :day_end
                    """
                ),
                {"master_id": master_id, "day_start": day_start, "day_end": day_end},
            ).mappings().all()

            for row in booking_rows:
                blocked_ranges.append((_as_datetime(row["slot_start"]), _as_datetime(row["slot_end"])))

            for row in block_rows:
                blocked_ranges.append((_as_datetime(row["start_at"]), _as_datetime(row["end_at"])))

            slots: list[AvailabilitySlot] = []
            slot_start = datetime.combine(on_date, work_start, tzinfo=UTC)
            slot_cutoff = datetime.combine(on_date, work_end, tzinfo=UTC)

            now_utc = _normalize_now(now)
            while slot_start + SLOT_DURATION <= slot_cutoff:
                slot_end = slot_start + SLOT_DURATION
                if now_utc is not None and slot_start.date() == now_utc.date() and slot_start < now_utc:
                    slot_start = slot_end
                    continue

                if not _is_blocked(slot_start, slot_end, blocked_ranges):
                    slots.append(AvailabilitySlot(start_at=slot_start, end_at=slot_end))

                slot_start = slot_end

            return slots


def _normalize_now(now: datetime | None) -> datetime | None:
    if now is None:
        return None
    if now.tzinfo is None:
        return now.replace(tzinfo=UTC)
    return now.astimezone(UTC)


def _is_blocked(start_at: datetime, end_at: datetime, blocked_ranges: list[tuple[datetime, datetime]]) -> bool:
    for blocked_start, blocked_end in blocked_ranges:
        if start_at < blocked_end and blocked_start < end_at:
            return True
    return False


def _as_time(value: time | str) -> time:
    if isinstance(value, time):
        return value
    return time.fromisoformat(value)


def _as_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
