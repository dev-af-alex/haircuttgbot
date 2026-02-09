from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.main import CreateBookingRequest, create_booking, health, metrics
from app.observability import emit_event, observe_master_admin_outcome

sqlite3.register_adapter(datetime, lambda value: value.isoformat())


def _setup_booking_schema() -> Engine:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE masters (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    work_start TEXT NOT NULL,
                    work_end TEXT NOT NULL,
                    lunch_start TEXT NOT NULL,
                    lunch_end TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE bookings (
                    id INTEGER PRIMARY KEY,
                    master_id INTEGER NOT NULL,
                    client_user_id INTEGER,
                    service_type TEXT,
                    status TEXT NOT NULL,
                    cancellation_reason TEXT,
                    slot_start DATETIME NOT NULL,
                    slot_end DATETIME NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE availability_blocks (
                    id INTEGER PRIMARY KEY,
                    master_id INTEGER NOT NULL,
                    block_type TEXT,
                    start_at DATETIME NOT NULL,
                    end_at DATETIME NOT NULL,
                    reason TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO masters (id, user_id, is_active, work_start, work_end, lunch_start, lunch_end)
                VALUES (1, 10, 1, '10:00:00', '21:00:00', '13:00:00', '14:00:00')
                """
            )
        )

    return engine


def _metric_value(
    exposition: str,
    metric_name: str,
    labels: dict[str, str] | None = None,
    default: float | None = None,
) -> float:
    for line in exposition.splitlines():
        if labels:
            if not line.startswith(f"{metric_name}{{"):
                continue
            if not all(f'{key}="{value}"' in line for key, value in labels.items()):
                continue
            return float(line.rsplit(" ", 1)[1])

        if line.startswith(f"{metric_name} "):
            return float(line.rsplit(" ", 1)[1])

    if default is not None:
        return default
    raise AssertionError(f"Metric {metric_name} not found")


def test_emit_event_redacts_sensitive_values(monkeypatch, caplog) -> None:
    token_value = "123456:super_secret_token"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", token_value)
    caplog.set_level(logging.INFO, logger="bot_api")

    emit_event(
        "observability_contract_test",
        telegram_token_configured=True,
        telegram_bot_token=token_value,
        nested={
            "authorization": f"Bearer {token_value}",
            "password": "my_password",
            "safe": "ok",
        },
        note=f"token={token_value}",
    )

    payload = json.loads(caplog.records[-1].message)

    assert payload["event"] == "observability_contract_test"
    assert payload["service"] == "bot-api"
    assert "ts" in payload
    assert payload["telegram_token_configured"] is True
    assert payload["telegram_bot_token"] == "[REDACTED]"
    assert payload["nested"]["authorization"] == "[REDACTED]"
    assert payload["nested"]["password"] == "[REDACTED]"
    assert payload["nested"]["safe"] == "ok"
    assert payload["note"] == "token=[REDACTED]"
    assert token_value not in caplog.records[-1].message


def test_metrics_endpoint_tracks_request_latency_and_booking_outcomes(monkeypatch) -> None:
    engine = _setup_booking_schema()
    monkeypatch.setattr("app.main.get_engine", lambda: engine)

    before = metrics().body.decode("utf-8")
    before_requests = _metric_value(
        before,
        "bot_api_requests_total",
        {
            "method": "POST",
            "path": "/internal/booking/create",
            "status_code": "200",
        },
        default=0.0,
    )
    before_success = _metric_value(
        before,
        "bot_api_booking_outcomes_total",
        {
            "action": "booking_create",
            "outcome": "success",
        },
        default=0.0,
    )
    before_failure = _metric_value(
        before,
        "bot_api_booking_outcomes_total",
        {
            "action": "booking_create",
            "outcome": "failure",
        },
        default=0.0,
    )

    first = create_booking(
        CreateBookingRequest(
            master_id=1,
            client_user_id=5001,
            service_type="haircut",
            slot_start=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
        )
    )
    second = create_booking(
        CreateBookingRequest(
            master_id=1,
            client_user_id=5002,
            service_type="beard",
            slot_start=datetime(2026, 2, 11, 10, 0, tzinfo=UTC),
        )
    )

    assert first["created"] is True
    assert second["created"] is False

    health()

    after = metrics().body.decode("utf-8")
    after_requests = _metric_value(
        after,
        "bot_api_requests_total",
        {
            "method": "POST",
            "path": "/internal/booking/create",
            "status_code": "200",
        },
    )
    after_success = _metric_value(
        after,
        "bot_api_booking_outcomes_total",
        {
            "action": "booking_create",
            "outcome": "success",
        },
    )
    after_failure = _metric_value(
        after,
        "bot_api_booking_outcomes_total",
        {
            "action": "booking_create",
            "outcome": "failure",
        },
    )
    health_value = _metric_value(after, "bot_api_service_health")

    assert after_requests >= before_requests + 2.0
    assert after_success >= before_success + 1.0
    assert after_failure >= before_failure + 1.0
    assert 'bot_api_request_latency_seconds_count{method="POST",path="/internal/booking/create"}' in after
    assert health_value == 1.0


def test_metrics_include_master_admin_outcomes_counter() -> None:
    before = metrics().body.decode("utf-8")
    before_value = _metric_value(
        before,
        "bot_api_master_admin_outcomes_total",
        {"action": "add", "outcome": "success"},
        default=0.0,
    )

    observe_master_admin_outcome("add", "success")

    after = metrics().body.decode("utf-8")
    after_value = _metric_value(
        after,
        "bot_api_master_admin_outcomes_total",
        {"action": "add", "outcome": "success"},
    )
    assert after_value >= before_value + 1.0
