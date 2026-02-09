from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.main import app
from app.throttling import TelegramCommandThrottle


def _metric_value(exposition: str, metric_name: str, labels: dict[str, str]) -> float:
    for line in exposition.splitlines():
        if not line.startswith(f"{metric_name}{{"):
            continue
        if all(f'{key}="{value}"' in line for key, value in labels.items()):
            return float(line.rsplit(" ", 1)[1])
    return 0.0


class _DummyTelegramFlowService:
    def __init__(self, _engine) -> None:
        pass

    def cancel(self, *, client_telegram_user_id: int, booking_id: int) -> dict[str, object]:
        return {
            "cancelled": True,
            "booking_id": booking_id,
            "message": "ok",
            "notifications": [{"recipient_telegram_user_id": client_telegram_user_id, "message": "ok"}],
        }


def _asgi_request(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, bytes]:
    response_messages: list[dict[str, Any]] = []
    request_body = json.dumps(payload or {}).encode("utf-8")
    request_sent = False

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(request_body)).encode("utf-8")),
        ],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }

    async def receive() -> dict[str, Any]:
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": request_body, "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        response_messages.append(message)

    asyncio.run(app(scope, receive, send))

    status_code = next(message["status"] for message in response_messages if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"")
        for message in response_messages
        if message["type"] == "http.response.body"
    )
    return status_code, body


def test_telegram_abuse_throttle_denies_burst_requests(monkeypatch, caplog) -> None:
    monkeypatch.setattr("app.main.TelegramBookingFlowService", _DummyTelegramFlowService)
    original_throttle = app.state.telegram_throttle
    app.state.telegram_throttle = TelegramCommandThrottle(limit=2, window_seconds=60)
    caplog.set_level(logging.INFO, logger="bot_api")

    try:
        payload = {"client_telegram_user_id": 2000001, "booking_id": 42}
        first_status, _ = _asgi_request("POST", "/internal/telegram/client/booking-flow/cancel", payload)
        second_status, _ = _asgi_request("POST", "/internal/telegram/client/booking-flow/cancel", payload)
        third_status, third_body = _asgi_request("POST", "/internal/telegram/client/booking-flow/cancel", payload)

        assert first_status == 200
        assert second_status == 200
        assert third_status == 429
        assert json.loads(third_body.decode("utf-8"))["code"] == "throttled"

        _, metrics_body = _asgi_request("GET", "/metrics")
        metrics_text = metrics_body.decode("utf-8")
    finally:
        app.state.telegram_throttle = original_throttle

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
