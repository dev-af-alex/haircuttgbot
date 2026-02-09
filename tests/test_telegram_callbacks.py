from __future__ import annotations

import json
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.telegram.callbacks import CallbackStateStore, TelegramCallbackRouter, decode_callback_data


def _setup_schema() -> Engine:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)"))
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    telegram_user_id BIGINT UNIQUE NOT NULL,
                    role_id INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(text("INSERT INTO roles (id, name) VALUES (1, 'Client'), (2, 'Master')"))
        conn.execute(
            text(
                """
                INSERT INTO users (id, telegram_user_id, role_id)
                VALUES
                    (10, 1000001, 2),
                    (20, 2000001, 1)
                """
            )
        )
    return engine


def test_decode_callback_data_rejects_malformed_payload() -> None:
    payload, error = decode_callback_data("wrong-prefix|cm")
    assert payload is None
    assert error == "unsupported_version"

    payload, error = decode_callback_data("hb1|unknown")
    assert payload is None
    assert error == "unknown_action"

    payload, error = decode_callback_data("hb1|cm|bad context")
    assert payload is None
    assert error == "invalid_context"


def test_callback_router_rejects_stale_action_and_logs_event(caplog) -> None:
    caplog.set_level(logging.INFO, logger="bot_api")
    state = CallbackStateStore()
    router = TelegramCallbackRouter(_setup_schema(), state_store=state)
    state.set_menu(telegram_user_id=2000001, menu="root")

    result = router.handle(telegram_user_id=2000001, data="hb1|bk")

    assert "устарела" in result.text
    events = [json.loads(record.message) for record in caplog.records if record.name == "bot_api"]
    assert any(event["event"] == "telegram_callback_stale" for event in events)


def test_callback_router_logs_rbac_deny_for_forbidden_action(caplog) -> None:
    caplog.set_level(logging.INFO, logger="bot_api")
    router = TelegramCallbackRouter(_setup_schema())

    result = router.handle(telegram_user_id=2000001, data="hb1|mm")

    assert "Недостаточно прав" in result.text
    events = [json.loads(record.message) for record in caplog.records if record.name == "bot_api"]
    deny_events = [event for event in events if event["event"] == "rbac_deny"]
    assert deny_events
    assert deny_events[-1]["command"] == "callback:mm"
