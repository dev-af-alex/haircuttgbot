from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from starlette.requests import Request

from app.main import app, telegram_command_guards
from app.observability import render_metrics
from app.throttling import TelegramCommandThrottle


def _metric_value(exposition: str, metric_name: str, labels: dict[str, str]) -> float:
    for line in exposition.splitlines():
        if not line.startswith(f"{metric_name}{{"):
            continue
        if all(f'{key}="{value}"' in line for key, value in labels.items()):
            return float(line.rsplit(" ", 1)[1])
    return 0.0


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


def test_telegram_abuse_throttle_denies_burst_requests(caplog) -> None:
    original_throttle = app.state.telegram_throttle
    app.state.telegram_throttle = TelegramCommandThrottle(limit=2, window_seconds=60)
    caplog.set_level(logging.INFO, logger="bot_api")

    class _DummyResponse:
        def __init__(self, response_payload: dict[str, Any]) -> None:
            self.status_code = 200
            self.media_type = "application/json"
            self.headers: dict[str, str] = {}

            async def _iterate():
                yield json.dumps(response_payload).encode("utf-8")

            self.body_iterator = _iterate()

    calls = {"count": 0}

    async def call_next(_request: Request):
        calls["count"] += 1
        payload = {
            "cancelled": True,
            "booking_id": 40 + calls["count"],
            "message": "ok",
            "notifications": [{"recipient_telegram_user_id": 2000001, "message": "ok"}],
        }
        return _DummyResponse(payload)

    try:
        first = asyncio.run(
            telegram_command_guards(
                _build_request(
                    "/internal/telegram/client/booking-flow/cancel",
                    {"client_telegram_user_id": 2000001, "booking_id": 42},
                ),
                call_next,
            )
        )
        second = asyncio.run(
            telegram_command_guards(
                _build_request(
                    "/internal/telegram/client/booking-flow/cancel",
                    {"client_telegram_user_id": 2000001, "booking_id": 43},
                ),
                call_next,
            )
        )
        third = asyncio.run(
            telegram_command_guards(
                _build_request(
                    "/internal/telegram/client/booking-flow/cancel",
                    {"client_telegram_user_id": 2000001, "booking_id": 44},
                ),
                call_next,
            )
        )
    finally:
        app.state.telegram_throttle = original_throttle

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert json.loads(third.body.decode("utf-8"))["code"] == "throttled"

    metrics_text = render_metrics()[0].decode("utf-8")
    allow_value = _metric_value(
        metrics_text,
        "bot_api_abuse_outcomes_total",
        {"path": "/internal/telegram/client/booking-flow/cancel", "outcome": "allow"},
    )
    deny_value = _metric_value(
        metrics_text,
        "bot_api_abuse_outcomes_total",
        {"path": "/internal/telegram/client/booking-flow/cancel", "outcome": "deny"},
    )

    assert allow_value >= 2.0
    assert deny_value >= 1.0

    deny_logs = [
        json.loads(record.message)
        for record in caplog.records
        if '"event": "abuse_throttle_deny"' in record.message
    ]
    assert deny_logs
    assert deny_logs[-1]["telegram_user_id"] == 2000001
