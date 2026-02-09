from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from time import monotonic
from typing import Any


@dataclass(frozen=True)
class CachedHttpResponse:
    status_code: int
    body: bytes
    media_type: str


class TelegramIdempotencyStore:
    def __init__(self, window_seconds: int) -> None:
        self.window_seconds = max(1, int(window_seconds))
        self._lock = threading.Lock()
        self._items: dict[str, tuple[float, CachedHttpResponse]] = {}

    def make_key(self, *, path: str, telegram_user_id: int, payload: dict[str, Any]) -> str:
        payload_encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        raw = f"{path}|{telegram_user_id}|{payload_encoded}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, key: str, now_seconds: float | None = None) -> CachedHttpResponse | None:
        now_value = monotonic() if now_seconds is None else now_seconds
        with self._lock:
            self._evict_expired(now_value)
            item = self._items.get(key)
            if item is None:
                return None
            return item[1]

    def put(self, key: str, response: CachedHttpResponse, now_seconds: float | None = None) -> None:
        now_value = monotonic() if now_seconds is None else now_seconds
        with self._lock:
            self._evict_expired(now_value)
            self._items[key] = (now_value, response)

    def _evict_expired(self, now_value: float) -> None:
        cutoff = now_value - self.window_seconds
        stale = [key for key, (created_at, _) in self._items.items() if created_at <= cutoff]
        for key in stale:
            self._items.pop(key, None)
