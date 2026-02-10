from __future__ import annotations

import os
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

BUSINESS_TIMEZONE_ENV = "BUSINESS_TIMEZONE"
BUSINESS_TIMEZONE_DEFAULT = "Europe/Moscow"


def resolve_business_timezone(raw_timezone: str | None) -> ZoneInfo:
    timezone_name = (raw_timezone or "").strip()
    if not timezone_name:
        timezone_name = BUSINESS_TIMEZONE_DEFAULT
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            f"{BUSINESS_TIMEZONE_ENV} must be a valid IANA timezone, got: {timezone_name!r}"
        ) from exc


def get_business_timezone() -> ZoneInfo:
    return resolve_business_timezone(os.getenv(BUSINESS_TIMEZONE_ENV))


def normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_business(value: datetime) -> datetime:
    return normalize_utc(value).astimezone(get_business_timezone())


def business_now() -> datetime:
    return utc_now().astimezone(get_business_timezone())


def business_date(value: datetime) -> date:
    return to_business(value).date()


def combine_business_date_time(on_date: date, at_time: time) -> datetime:
    local = datetime.combine(on_date, at_time, tzinfo=get_business_timezone())
    return local.astimezone(UTC)


def business_day_bounds(on_date: date) -> tuple[datetime, datetime]:
    start_local = datetime.combine(on_date, time.min, tzinfo=get_business_timezone())
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)
