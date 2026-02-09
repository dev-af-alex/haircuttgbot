from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.telegram.callbacks import build_client_date_markup, build_slot_markup
from app.telegram.presentation import chunk_inline_buttons, format_ru_datetime, format_ru_slot_range


def _button_texts(markup) -> list[str]:
    texts: list[str] = []
    for row in markup.inline_keyboard:
        for button in row:
            texts.append(button.text)
    return texts


def test_format_ru_slot_range_for_30_and_60_minute_slots() -> None:
    start = datetime(2026, 2, 11, 10, 0, tzinfo=UTC)
    assert format_ru_slot_range(start, duration_minutes=30) == "10:00-10:30"
    assert format_ru_slot_range(start, duration_minutes=60) == "10:00-11:00"


def test_format_ru_datetime_output() -> None:
    value = datetime(2026, 2, 11, 18, 45, tzinfo=UTC)
    assert format_ru_datetime(value) == "11.02.2026 18:45"


def test_chunk_inline_buttons_splits_rows_by_max_size() -> None:
    from aiogram.types import InlineKeyboardButton

    buttons = [InlineKeyboardButton(text=f"B{i}", callback_data=f"hb1|hm|{i}") for i in range(5)]
    rows = chunk_inline_buttons(buttons, max_per_row=2)

    assert [len(row) for row in rows] == [2, 2, 1]


def test_chunk_inline_buttons_rejects_non_positive_row_size() -> None:
    from aiogram.types import InlineKeyboardButton

    with pytest.raises(ValueError):
        chunk_inline_buttons(
            [InlineKeyboardButton(text="A", callback_data="hb1|hm")],
            max_per_row=0,
        )


def test_build_client_date_markup_uses_localized_ru_dates() -> None:
    markup = build_client_date_markup(action="csd", days_ahead=1)
    labels = _button_texts(markup)
    expected = datetime.now(UTC).date().strftime("%d.%m.%Y")
    assert expected in labels


def test_build_slot_markup_includes_range_labels() -> None:
    markup = build_slot_markup(
        [
            {
                "start_at": "2026-02-11T10:00:00+00:00",
                "end_at": "2026-02-11T10:30:00+00:00",
            },
            {
                "start_at": "2026-02-11T11:00:00+00:00",
                "end_at": "2026-02-11T12:00:00+00:00",
            },
        ],
        action="csl",
    )

    labels = _button_texts(markup)
    assert "10:00-10:30" in labels
    assert "11:00-12:00" in labels
