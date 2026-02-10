from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.booking.guardrails import same_day_min_slot_start
from app.booking.intervals import is_interval_blocked
from app.booking.service_options import (
    DEFAULT_SLOT_STEP_MINUTES,
    resolve_service_duration_minutes,
)
from app.timezone import business_day_bounds, combine_business_date_time, normalize_utc


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
        service_type: str,
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

            duration_minutes = resolve_service_duration_minutes(service_type, connection=conn)
            if duration_minutes is None:
                return []
            slot_duration = timedelta(minutes=duration_minutes)
            slot_step = timedelta(minutes=DEFAULT_SLOT_STEP_MINUTES)

            work_start = _as_time(master["work_start"])
            work_end = _as_time(master["work_end"])
            lunch_start = _as_time(master["lunch_start"])
            lunch_end = _as_time(master["lunch_end"])

            day_start, day_end = business_day_bounds(on_date)

            blocked_ranges = [
                (
                    combine_business_date_time(on_date, lunch_start),
                    combine_business_date_time(on_date, lunch_end),
                )
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
            slot_start = combine_business_date_time(on_date, work_start)
            slot_cutoff = combine_business_date_time(on_date, work_end)

            now_utc = _normalize_now(now)
            same_day_min_start = None
            if now_utc is not None:
                same_day_min_start = same_day_min_slot_start(
                    on_date=on_date,
                    now=now_utc,
                    slot_step_minutes=slot_step.seconds // 60,
                )
            while slot_start + slot_duration <= slot_cutoff:
                slot_end = slot_start + slot_duration
                if same_day_min_start is not None and slot_start < same_day_min_start:
                    slot_start = slot_start + slot_step
                    continue

                if not is_interval_blocked(start_at=slot_start, end_at=slot_end, blocked_ranges=blocked_ranges):
                    slots.append(AvailabilitySlot(start_at=slot_start, end_at=slot_end))

                slot_start = slot_start + slot_step

            return slots


def _normalize_now(now: datetime | None) -> datetime | None:
    if now is None:
        return None
    return normalize_utc(now)


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
