from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.booking.guardrails import same_day_min_slot_start
from app.telegram.presentation import format_ru_datetime, format_ru_slot_range
from app.timezone import (
    business_day_bounds,
    get_business_timezone,
    resolve_business_timezone,
)


def test_get_business_timezone_uses_default_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BUSINESS_TIMEZONE", raising=False)
    assert str(get_business_timezone()) == "Europe/Moscow"


def test_resolve_business_timezone_rejects_invalid_iana_name() -> None:
    with pytest.raises(ValueError):
        resolve_business_timezone("Mars/Phobos")


def test_same_day_guardrail_uses_business_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUSINESS_TIMEZONE", "Europe/Moscow")

    now_utc = datetime(2026, 2, 10, 12, 0, tzinfo=UTC)  # 15:00 in Moscow
    min_start = same_day_min_slot_start(
        on_date=date(2026, 2, 10),
        now=now_utc,
        slot_step_minutes=30,
    )
    assert min_start == datetime(2026, 2, 10, 12, 30, tzinfo=UTC)  # 15:30 in Moscow


def test_presentation_formats_use_configured_business_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUSINESS_TIMEZONE", "Europe/Moscow")

    value = datetime(2026, 2, 11, 18, 45, tzinfo=UTC)
    assert format_ru_datetime(value) == "11.02.2026 21:45"
    assert format_ru_slot_range(datetime(2026, 2, 11, 7, 0, tzinfo=UTC), duration_minutes=60) == "10:00-11:00"


def test_business_day_bounds_handle_berlin_dst_spring_forward(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUSINESS_TIMEZONE", "Europe/Berlin")

    day_start, day_end = business_day_bounds(date(2026, 3, 29))
    assert (day_end - day_start).total_seconds() == 23 * 3600


def test_business_day_bounds_handle_berlin_dst_fall_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUSINESS_TIMEZONE", "Europe/Berlin")

    day_start, day_end = business_day_bounds(date(2026, 10, 25))
    assert (day_end - day_start).total_seconds() == 25 * 3600
