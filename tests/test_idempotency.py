from __future__ import annotations

import asyncio
import json
from typing import Any

from app.idempotency import TelegramIdempotencyStore
from app.main import app


def _asgi_request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, str], bytes]:
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

    start = next(message for message in response_messages if message["type"] == "http.response.start")
    status_code = int(start["status"])
    headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in start["headers"]}
    body = b"".join(
        message.get("body", b"")
        for message in response_messages
        if message["type"] == "http.response.body"
    )
    return status_code, headers, body


class _DummyConfirmFlowService:
    calls = 0

    def __init__(self, _engine) -> None:
        pass

    def confirm(
        self,
        *,
        client_telegram_user_id: int,
        master_id: int,
        service_type: str,
        slot_start,
    ) -> dict[str, object]:
        _ = client_telegram_user_id
        _ = master_id
        _ = service_type
        _ = slot_start
        self.__class__.calls += 1
        return {
            "created": True,
            "booking_id": 5000 + self.__class__.calls,
            "message": "ok",
            "notifications": [],
        }


def test_telegram_idempotency_replays_successful_write(monkeypatch) -> None:
    monkeypatch.setattr("app.main.TelegramBookingFlowService", _DummyConfirmFlowService)
    _DummyConfirmFlowService.calls = 0

    original_store = app.state.telegram_idempotency
    app.state.telegram_idempotency = TelegramIdempotencyStore(window_seconds=120)

    try:
        payload = {
            "client_telegram_user_id": 2000001,
            "master_id": 1,
            "service_type": "haircut",
            "slot_start": "2026-02-13T10:00:00+00:00",
        }

        first_status, first_headers, first_body = _asgi_request(
            "POST",
            "/internal/telegram/client/booking-flow/confirm",
            payload,
        )
        second_status, second_headers, second_body = _asgi_request(
            "POST",
            "/internal/telegram/client/booking-flow/confirm",
            payload,
        )
    finally:
        app.state.telegram_idempotency = original_store

    first_json = json.loads(first_body.decode("utf-8"))
    second_json = json.loads(second_body.decode("utf-8"))

    assert first_status == 200
    assert second_status == 200
    assert first_headers.get("x-idempotency-replayed") is None
    assert second_headers.get("x-idempotency-replayed") == "1"
    assert first_json["created"] is True
    assert second_json["created"] is True
    assert first_json["booking_id"] == second_json["booking_id"]
    assert _DummyConfirmFlowService.calls == 1
