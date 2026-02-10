from __future__ import annotations

from datetime import date, datetime, time, timedelta

from aiogram.types import InlineKeyboardButton
from app.timezone import to_business

RU_DATE_FORMAT = "%d.%m.%Y"
RU_TIME_FORMAT = "%H:%M"
RU_DATETIME_FORMAT = "%d.%m.%Y %H:%M"

MOBILE_MENU_MAX_BUTTONS_PER_ROW = 2
MOBILE_DATE_SLOT_MAX_BUTTONS_PER_ROW = 3


def format_ru_date(value: date) -> str:
    return value.strftime(RU_DATE_FORMAT)


def format_ru_time(value: datetime | time) -> str:
    if isinstance(value, datetime):
        normalized = to_business(value)
        return normalized.strftime(RU_TIME_FORMAT)
    return value.strftime(RU_TIME_FORMAT)


def format_ru_datetime(value: datetime) -> str:
    return to_business(value).strftime(RU_DATETIME_FORMAT)


def format_ru_slot_range(start_at: datetime, *, duration_minutes: int) -> str:
    end_at = start_at + timedelta(minutes=duration_minutes)
    return f"{format_ru_time(start_at)}-{format_ru_time(end_at)}"


def chunk_inline_buttons(
    buttons: list[InlineKeyboardButton],
    *,
    max_per_row: int,
) -> list[list[InlineKeyboardButton]]:
    if max_per_row <= 0:
        raise ValueError("max_per_row must be positive")
    if not buttons:
        return []

    rows: list[list[InlineKeyboardButton]] = []
    for index in range(0, len(buttons), max_per_row):
        rows.append(buttons[index : index + max_per_row])
    return rows
