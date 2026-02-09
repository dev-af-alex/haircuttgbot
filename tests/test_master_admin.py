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
                    telegram_username TEXT,
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
                INSERT INTO users (id, telegram_user_id, telegram_username, role_id)
                VALUES
                    (10, 1000001, 'owner_master', 2),
                    (11, 1000002, 'worker_master', 2),
                    (20, 2000001, 'client_a', 1),
                    (21, 2000002, 'new_master_candidate', 1)
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


def test_add_master_by_nickname_handles_success_unknown_and_ambiguous() -> None:
    engine = _setup_schema()
    service = MasterAdminService(engine)

    success = service.add_master_by_nickname(raw_nickname="@new_master_candidate")
    assert success.applied is True
    assert success.target_telegram_user_id == 2000002
    assert success.reason in {"added", "already_active", "reactivated"}

    unknown = service.add_master_by_nickname(raw_nickname="@unknown_nick")
    assert unknown.applied is False
    assert unknown.reason == "nickname_not_found"

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO users (id, telegram_user_id, telegram_username, role_id)
                VALUES (31, 2000003, 'dupe_nick', 1), (32, 2000004, 'dupe_nick', 1)
                """
            )
        )
    ambiguous = service.add_master_by_nickname(raw_nickname="@dupe_nick")
    assert ambiguous.applied is False
    assert ambiguous.reason == "nickname_ambiguous"


def test_add_master_by_nickname_rejects_invalid_format() -> None:
    service = MasterAdminService(_setup_schema())

    invalid = service.add_master_by_nickname(raw_nickname="not_a_nickname")
    assert invalid.applied is False
    assert invalid.reason == "invalid_nickname_format"


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


def test_rename_master_display_name_handles_success_and_validation_paths() -> None:
    engine = _setup_schema()
    service = MasterAdminService(engine)

    renamed = service.rename_master_display_name(
        telegram_user_id=1000002,
        raw_display_name="Top Barber",
    )
    assert renamed.applied is True
    assert renamed.reason == "renamed"

    unchanged = service.rename_master_display_name(
        telegram_user_id=1000002,
        raw_display_name="Top Barber",
    )
    assert unchanged.applied is False
    assert unchanged.reason == "display_name_unchanged"

    invalid = service.rename_master_display_name(
        telegram_user_id=1000002,
        raw_display_name="   ",
    )
    assert invalid.applied is False
    assert invalid.reason == "invalid_display_name_format"

    missing = service.rename_master_display_name(
        telegram_user_id=2999999,
        raw_display_name="Ghost Master",
    )
    assert missing.applied is False
    assert missing.reason == "master_not_found"

    with engine.begin() as conn:
        display_name = conn.execute(
            text(
                """
                SELECT m.display_name
                FROM masters m
                JOIN users u ON u.id = m.user_id
                WHERE u.telegram_user_id = 1000002
                """
            )
        ).scalar_one()
        assert display_name == "Top Barber"
