from __future__ import annotations

import asyncio
import json
from typing import Any

from starlette.requests import Request

from app.idempotency import TelegramIdempotencyStore
from app.main import app, telegram_command_guards
from app.observability import render_metrics
from app.throttling import TelegramCommandThrottle


def _metric_value(exposition: str, metric_name: str, labels: dict[str, str], default: float = 0.0) -> float:
    for line in exposition.splitlines():
        if not line.startswith(f"{metric_name}{{"):
            continue
        if all(f'{key}="{value}"' in line for key, value in labels.items()):
            return float(line.rsplit(" ", 1)[1])
    return default


def _build_request(path: str, payload: dict[str, Any]) -> Request:
    body = json.dumps(payload).encode("utf-8")
    delivered = False

    async def receive() -> dict[str, Any]:
        nonlocal delivered
        if delivered:
            return {"type": "http.request", "body": b"", "more_body": False}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("utf-8")),
        ],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
        "root_path": "",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
    }
    return Request(scope, receive)


def test_telegram_idempotency_replays_successful_write() -> None:
    original_store = app.state.telegram_idempotency
    original_throttle = app.state.telegram_throttle
    app.state.telegram_idempotency = TelegramIdempotencyStore(window_seconds=120)
    app.state.telegram_throttle = TelegramCommandThrottle(limit=100, window_seconds=60)

    try:
        before_metrics = render_metrics()[0].decode("utf-8")
        before_processed = _metric_value(
            before_metrics,
            "bot_api_telegram_delivery_outcomes_total",
            {"path": "/internal/telegram/client/booking-flow/confirm", "outcome": "processed_success"},
        )
        before_replayed = _metric_value(
            before_metrics,
            "bot_api_telegram_delivery_outcomes_total",
            {"path": "/internal/telegram/client/booking-flow/confirm", "outcome": "replayed"},
        )

        payload = {
            "client_telegram_user_id": 2000001,
            "master_id": 1,
            "service_type": "haircut",
            "slot_start": "2026-02-13T10:00:00+00:00",
        }
        calls = {"count": 0}

        class _DummyResponse:
            def __init__(self, response_payload: dict[str, Any]) -> None:
                self.status_code = 200
                self.media_type = "application/json"
                self.headers: dict[str, str] = {}

                async def _iterate():
                    yield json.dumps(response_payload).encode("utf-8")

                self.body_iterator = _iterate()

        async def call_next(_request: Request):
            calls["count"] += 1
            payload = {
                "created": True,
                "booking_id": 5000 + calls["count"],
                "message": "ok",
                "notifications": [],
            }
            return _DummyResponse(payload)

        first = asyncio.run(
            telegram_command_guards(
                _build_request("/internal/telegram/client/booking-flow/confirm", payload),
                call_next,
            )
        )
        second = asyncio.run(
            telegram_command_guards(
                _build_request("/internal/telegram/client/booking-flow/confirm", payload),
                call_next,
            )
        )
    finally:
        app.state.telegram_idempotency = original_store
        app.state.telegram_throttle = original_throttle

    first_body = json.loads(first.body.decode("utf-8"))
    second_body = json.loads(second.body.decode("utf-8"))
    after_metrics = render_metrics()[0].decode("utf-8")
    after_processed = _metric_value(
        after_metrics,
        "bot_api_telegram_delivery_outcomes_total",
        {"path": "/internal/telegram/client/booking-flow/confirm", "outcome": "processed_success"},
    )
    after_replayed = _metric_value(
        after_metrics,
        "bot_api_telegram_delivery_outcomes_total",
        {"path": "/internal/telegram/client/booking-flow/confirm", "outcome": "replayed"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers.get("X-Idempotency-Replayed") is None
    assert second.headers.get("X-Idempotency-Replayed") == "1"
    assert first_body["created"] is True
    assert second_body["created"] is True
    assert first_body["booking_id"] == second_body["booking_id"]
    assert calls["count"] == 1
    assert after_processed >= before_processed + 1.0
    assert after_replayed >= before_replayed + 1.0


def test_telegram_idempotency_does_not_cache_rejected_write() -> None:
    original_store = app.state.telegram_idempotency
    original_throttle = app.state.telegram_throttle
    app.state.telegram_idempotency = TelegramIdempotencyStore(window_seconds=120)
    app.state.telegram_throttle = TelegramCommandThrottle(limit=100, window_seconds=60)

    try:
        before_metrics = render_metrics()[0].decode("utf-8")
        before_rejected = _metric_value(
            before_metrics,
            "bot_api_telegram_delivery_outcomes_total",
            {"path": "/internal/telegram/client/booking-flow/confirm", "outcome": "processed_rejected"},
        )

        payload = {
            "client_telegram_user_id": 2000002,
            "master_id": 1,
            "service_type": "haircut",
            "slot_start": "2026-02-13T11:00:00+00:00",
        }
        calls = {"count": 0}

        class _DummyResponse:
            def __init__(self, response_payload: dict[str, Any]) -> None:
                self.status_code = 200
                self.media_type = "application/json"
                self.headers: dict[str, str] = {}

                async def _iterate():
                    yield json.dumps(response_payload).encode("utf-8")

                self.body_iterator = _iterate()

        async def call_next(_request: Request):
            calls["count"] += 1
            payload = {
                "created": False,
                "booking_id": None,
                "message": "slot is not available",
                "notifications": [],
            }
            return _DummyResponse(payload)

        first = asyncio.run(
            telegram_command_guards(
                _build_request("/internal/telegram/client/booking-flow/confirm", payload),
                call_next,
            )
        )
        second = asyncio.run(
            telegram_command_guards(
                _build_request("/internal/telegram/client/booking-flow/confirm", payload),
                call_next,
            )
        )
    finally:
        app.state.telegram_idempotency = original_store
        app.state.telegram_throttle = original_throttle

    first_body = json.loads(first.body.decode("utf-8"))
    second_body = json.loads(second.body.decode("utf-8"))
    after_metrics = render_metrics()[0].decode("utf-8")
    after_rejected = _metric_value(
        after_metrics,
        "bot_api_telegram_delivery_outcomes_total",
        {"path": "/internal/telegram/client/booking-flow/confirm", "outcome": "processed_rejected"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers.get("X-Idempotency-Replayed") is None
    assert second.headers.get("X-Idempotency-Replayed") is None
    assert first_body["created"] is False
    assert second_body["created"] is False
    assert calls["count"] == 2
    assert after_rejected >= before_rejected + 2.0


def test_telegram_idempotency_key_includes_service_type_for_variable_durations() -> None:
    original_store = app.state.telegram_idempotency
    original_throttle = app.state.telegram_throttle
    app.state.telegram_idempotency = TelegramIdempotencyStore(window_seconds=120)
    app.state.telegram_throttle = TelegramCommandThrottle(limit=100, window_seconds=60)

    try:
        payload_a = {
            "client_telegram_user_id": 2000001,
            "master_id": 1,
            "service_type": "haircut",
            "slot_start": "2026-02-13T10:00:00+00:00",
        }
        payload_b = {
            "client_telegram_user_id": 2000001,
            "master_id": 1,
            "service_type": "haircut_beard",
            "slot_start": "2026-02-13T10:00:00+00:00",
        }
        calls = {"count": 0}

        class _DummyResponse:
            def __init__(self, response_payload: dict[str, Any]) -> None:
                self.status_code = 200
                self.media_type = "application/json"
                self.headers: dict[str, str] = {}

                async def _iterate():
                    yield json.dumps(response_payload).encode("utf-8")

                self.body_iterator = _iterate()

        async def call_next(_request: Request):
            calls["count"] += 1
            payload = {
                "created": True,
                "booking_id": 8000 + calls["count"],
                "message": "ok",
                "notifications": [],
            }
            return _DummyResponse(payload)

        first = asyncio.run(
            telegram_command_guards(
                _build_request("/internal/telegram/client/booking-flow/confirm", payload_a),
                call_next,
            )
        )
        second = asyncio.run(
            telegram_command_guards(
                _build_request("/internal/telegram/client/booking-flow/confirm", payload_b),
                call_next,
            )
        )
    finally:
        app.state.telegram_idempotency = original_store
        app.state.telegram_throttle = original_throttle

    first_body = json.loads(first.body.decode("utf-8"))
    second_body = json.loads(second.body.decode("utf-8"))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers.get("X-Idempotency-Replayed") is None
    assert second.headers.get("X-Idempotency-Replayed") is None
    assert first_body["booking_id"] != second_body["booking_id"]
    assert calls["count"] == 2
