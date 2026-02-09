from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class ThrottleDecision:
    allowed: bool
    retry_after_seconds: int


class TelegramCommandThrottle:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self._events: dict[int, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, telegram_user_id: int, now_seconds: float | None = None) -> ThrottleDecision:
        now_value = monotonic() if now_seconds is None else now_seconds
        window_start = now_value - self.window_seconds

        with self._lock:
            events = self._events.setdefault(telegram_user_id, deque())
            while events and events[0] <= window_start:
                events.popleft()

            if len(events) >= self.limit:
                retry_after = int(max(1.0, events[0] + self.window_seconds - now_value))
                return ThrottleDecision(allowed=False, retry_after_seconds=retry_after)

            events.append(now_value)
            return ThrottleDecision(allowed=True, retry_after_seconds=0)
