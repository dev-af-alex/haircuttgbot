from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta

from app.timezone import get_business_timezone, normalize_utc

DEFAULT_MIN_LEAD_MINUTES = 30

def same_day_min_slot_start(
    *,
    on_date: date,
    now: datetime,
    slot_step_minutes: int,
    min_lead_minutes: int = DEFAULT_MIN_LEAD_MINUTES,
) -> datetime | None:
    now_business = normalize_utc(now).astimezone(get_business_timezone())
    if on_date != now_business.date():
        return None

    threshold = now_business + timedelta(minutes=min_lead_minutes)
    day_start = datetime.combine(on_date, time.min, tzinfo=get_business_timezone())
    total_minutes = (threshold - day_start).total_seconds() / 60
    rounded_minutes = int(math.ceil(total_minutes / slot_step_minutes) * slot_step_minutes)
    return normalize_utc(day_start + timedelta(minutes=rounded_minutes))


def is_slot_start_allowed(
    *,
    slot_start: datetime,
    now: datetime,
    slot_step_minutes: int,
    min_lead_minutes: int = DEFAULT_MIN_LEAD_MINUTES,
) -> bool:
    slot_start_utc = normalize_utc(slot_start)
    min_start = same_day_min_slot_start(
        on_date=slot_start_utc.date(),
        now=now,
        slot_step_minutes=slot_step_minutes,
        min_lead_minutes=min_lead_minutes,
    )
    if min_start is None:
        return True
    return slot_start_utc >= min_start
