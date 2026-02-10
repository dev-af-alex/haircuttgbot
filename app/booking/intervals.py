from __future__ import annotations

from datetime import datetime


def intervals_overlap(*, start_at: datetime, end_at: datetime, other_start: datetime, other_end: datetime) -> bool:
    return start_at < other_end and other_start < end_at


def is_interval_blocked(*, start_at: datetime, end_at: datetime, blocked_ranges: list[tuple[datetime, datetime]]) -> bool:
    for blocked_start, blocked_end in blocked_ranges:
        if intervals_overlap(start_at=start_at, end_at=end_at, other_start=blocked_start, other_end=blocked_end):
            return True
    return False
