from __future__ import annotations

import sqlite3
from datetime import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.booking.master_admin import MasterAdminService

sqlite3.register_adapter(time, lambda value: value.isoformat())


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
        conn.execute(
            text(
                """
                CREATE TABLE masters (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    work_start TEXT NOT NULL,
                    work_end TEXT NOT NULL,
                    lunch_start TEXT NOT NULL,
                    lunch_end TEXT NOT NULL
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
                    (11, 1000002, 2),
                    (20, 2000001, 1),
                    (21, 2000002, 1)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO masters (id, user_id, display_name, is_active, work_start, work_end, lunch_start, lunch_end)
                VALUES
                    (1, 10, 'Master Owner', 1, '10:00:00', '21:00:00', '13:00:00', '14:00:00'),
                    (2, 11, 'Master Demo 2', 1, '10:00:00', '21:00:00', '13:00:00', '14:00:00')
                """
            )
        )

    return engine


def test_add_master_is_idempotent_and_updates_role() -> None:
    engine = _setup_schema()
    service = MasterAdminService(engine)

    first = service.add_master(telegram_user_id=2000002)
    second = service.add_master(telegram_user_id=2000002)

    assert first.applied is True
    assert second.applied is True

    with engine.begin() as conn:
        role_name = conn.execute(
            text(
                """
                SELECT r.name
                FROM users u
                JOIN roles r ON r.id = u.role_id
                WHERE u.telegram_user_id = 2000002
                """
            )
        ).scalar_one()
        assert role_name == "Master"

        masters_count = conn.execute(
            text(
                """
                SELECT count(*)
                FROM masters m
                JOIN users u ON u.id = m.user_id
                WHERE u.telegram_user_id = 2000002
                """
            )
        ).scalar_one()
        assert masters_count == 1


def test_remove_master_blocks_bootstrap_and_soft_deactivates() -> None:
    engine = _setup_schema()
    service = MasterAdminService(engine)

    blocked = service.remove_master(
        telegram_user_id=1000001,
        bootstrap_master_telegram_user_id=1000001,
    )
    assert blocked.applied is False
    assert "bootstrap" in blocked.message.lower()

    removed = service.remove_master(
        telegram_user_id=1000002,
        bootstrap_master_telegram_user_id=1000001,
    )
    assert removed.applied is True

    with engine.begin() as conn:
        is_active = conn.execute(
            text(
                """
                SELECT m.is_active
                FROM masters m
                JOIN users u ON u.id = m.user_id
                WHERE u.telegram_user_id = 1000002
                """
            )
        ).scalar_one()
        assert bool(is_active) is False
