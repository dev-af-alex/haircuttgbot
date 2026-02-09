from __future__ import annotations

import sqlite3
from datetime import time

from sqlalchemy import create_engine, text

from app.db.seed import resolve_bootstrap_master_telegram_id, run_seed

sqlite3.register_adapter(bool, int)
sqlite3.register_adapter(time, lambda value: value.isoformat())


def test_resolve_bootstrap_master_telegram_id_validates_input() -> None:
    assert resolve_bootstrap_master_telegram_id("1000001") == 1000001

    for invalid in (None, "", "  ", "abc", "0", "-1"):
        try:
            resolve_bootstrap_master_telegram_id(invalid)
            raise AssertionError("expected ValueError for invalid bootstrap telegram id")
        except ValueError:
            pass


def test_run_seed_idempotency_with_file_backed_sqlite(tmp_path) -> None:
    db_path = tmp_path / "seed.db"
    database_url = f"sqlite+pysqlite:///{db_path}"

    engine = create_engine(database_url, future=True)
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
                    work_start TEXT NOT NULL,
                    work_end TEXT NOT NULL,
                    lunch_start TEXT NOT NULL,
                    lunch_end TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE services (
                    id INTEGER PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    label_ru TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
                    is_active BOOLEAN NOT NULL
                )
                """
            )
        )
        conn.execute(text("INSERT INTO roles (id, name) VALUES (1, 'Client')"))
        conn.execute(text("INSERT INTO users (telegram_user_id, telegram_username, role_id) VALUES (1000001, NULL, 1)"))

    run_seed(database_url, bootstrap_master_telegram_id=1000001)
    run_seed(database_url, bootstrap_master_telegram_id=1000001)

    with engine.begin() as conn:
        role_names = {
            row[0]
            for row in conn.execute(text("SELECT name FROM roles"))
        }
        assert role_names == {"Client", "Master"}

        master_role_id = conn.execute(text("SELECT id FROM roles WHERE name='Master'")).scalar_one()
        bootstrap_role_id = conn.execute(
            text("SELECT role_id FROM users WHERE telegram_user_id = 1000001")
        ).scalar_one()
        assert bootstrap_role_id == master_role_id

        masters_count = conn.execute(text("SELECT count(*) FROM masters")).scalar_one()
        assert masters_count >= 2

        bootstrap_master_name = conn.execute(
            text(
                """
                SELECT m.display_name
                FROM masters m
                JOIN users u ON u.id = m.user_id
                WHERE u.telegram_user_id = 1000001
                """
            )
        ).scalar_one()
        assert bootstrap_master_name == "Master Owner"

        bootstrap_username = conn.execute(
            text("SELECT telegram_username FROM users WHERE telegram_user_id = 1000001")
        ).scalar_one()
        assert bootstrap_username == "master_1000001"

        service_rows = conn.execute(
            text(
                """
                SELECT code, label_ru, duration_minutes, is_active
                FROM services
                ORDER BY code
                """
            )
        ).all()
        assert service_rows == [
            ("beard", "Борода", 30, 1),
            ("haircut", "Стрижка", 30, 1),
            ("haircut_beard", "Стрижка + борода", 60, 1),
        ]
