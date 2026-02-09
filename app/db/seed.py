from __future__ import annotations

import os
from datetime import time

from sqlalchemy import create_engine, text

from app.booking.service_options import list_service_catalog_defaults

DEFAULT_DATABASE_URL = "postgresql+psycopg2://haircuttgbot:haircuttgbot@postgres:5432/haircuttgbot"
BOOTSTRAP_MASTER_TELEGRAM_ID_ENV = "BOOTSTRAP_MASTER_TELEGRAM_ID"
_DEFAULT_BOOTSTRAP_MASTER_DISPLAY_NAME = "Master Owner"
_DEFAULT_DEMO_MASTER_DISPLAY_NAME = "Master Demo 2"
_DEFAULT_DEMO_MASTER_TELEGRAM_ID = 1000002


def resolve_bootstrap_master_telegram_id(raw_value: str | None) -> int:
    value = (raw_value or "").strip()
    if not value:
        raise ValueError(
            f"{BOOTSTRAP_MASTER_TELEGRAM_ID_ENV} is required and must be a positive integer telegram user id"
        )
    try:
        telegram_user_id = int(value)
    except ValueError as exc:
        raise ValueError(
            f"{BOOTSTRAP_MASTER_TELEGRAM_ID_ENV} must be a positive integer telegram user id"
        ) from exc
    if telegram_user_id <= 0:
        raise ValueError(
            f"{BOOTSTRAP_MASTER_TELEGRAM_ID_ENV} must be a positive integer telegram user id"
        )
    return telegram_user_id


def _secondary_demo_master_telegram_id(bootstrap_master_telegram_id: int) -> int:
    if bootstrap_master_telegram_id != _DEFAULT_DEMO_MASTER_TELEGRAM_ID:
        return _DEFAULT_DEMO_MASTER_TELEGRAM_ID
    return _DEFAULT_DEMO_MASTER_TELEGRAM_ID + 1


def run_seed(database_url: str, *, bootstrap_master_telegram_id: int) -> None:
    engine = create_engine(database_url, future=True)
    demo_master_telegram_id = _secondary_demo_master_telegram_id(bootstrap_master_telegram_id)
    bootstrap_master_username = f"master_{bootstrap_master_telegram_id}"
    demo_master_username = f"master_{demo_master_telegram_id}"
    service_catalog = list_service_catalog_defaults()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO roles (name)
                VALUES ('Client'), ('Master')
                ON CONFLICT (name) DO NOTHING
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT INTO users (telegram_user_id, telegram_username, role_id)
                VALUES (
                    :bootstrap_master_telegram_id,
                    :bootstrap_master_username,
                    (SELECT id FROM roles WHERE name = 'Master')
                )
                ON CONFLICT (telegram_user_id) DO UPDATE
                    SET role_id = EXCLUDED.role_id,
                        telegram_username = COALESCE(users.telegram_username, EXCLUDED.telegram_username)
                """
            ),
            {
                "bootstrap_master_telegram_id": bootstrap_master_telegram_id,
                "bootstrap_master_username": bootstrap_master_username,
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO users (telegram_user_id, telegram_username, role_id)
                VALUES (
                    :demo_master_telegram_id,
                    :demo_master_username,
                    (SELECT id FROM roles WHERE name = 'Master')
                )
                ON CONFLICT (telegram_user_id) DO UPDATE
                    SET role_id = EXCLUDED.role_id,
                        telegram_username = COALESCE(users.telegram_username, EXCLUDED.telegram_username)
                """
            ),
            {
                "demo_master_telegram_id": demo_master_telegram_id,
                "demo_master_username": demo_master_username,
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO masters (user_id, display_name, work_start, work_end, lunch_start, lunch_end, is_active)
                VALUES (
                    (SELECT id FROM users WHERE telegram_user_id = :bootstrap_master_telegram_id),
                    :bootstrap_master_display_name,
                    :work_start,
                    :work_end,
                    :lunch_start,
                    :lunch_end,
                    true
                )
                ON CONFLICT (user_id) DO UPDATE
                    SET display_name = EXCLUDED.display_name,
                        work_start = EXCLUDED.work_start,
                        work_end = EXCLUDED.work_end,
                        lunch_start = EXCLUDED.lunch_start,
                        lunch_end = EXCLUDED.lunch_end,
                        is_active = true
                """
            ),
            {
                "bootstrap_master_telegram_id": bootstrap_master_telegram_id,
                "bootstrap_master_display_name": _DEFAULT_BOOTSTRAP_MASTER_DISPLAY_NAME,
                "work_start": time(10, 0),
                "work_end": time(21, 0),
                "lunch_start": time(13, 0),
                "lunch_end": time(14, 0),
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO masters (user_id, display_name, work_start, work_end, lunch_start, lunch_end, is_active)
                VALUES (
                    (SELECT id FROM users WHERE telegram_user_id = :demo_master_telegram_id),
                    :demo_master_display_name,
                    :work_start,
                    :work_end,
                    :lunch_start,
                    :lunch_end,
                    true
                )
                ON CONFLICT (user_id) DO UPDATE
                    SET display_name = EXCLUDED.display_name,
                        work_start = EXCLUDED.work_start,
                        work_end = EXCLUDED.work_end,
                        lunch_start = EXCLUDED.lunch_start,
                        lunch_end = EXCLUDED.lunch_end,
                        is_active = true
                """
            ),
            {
                "demo_master_telegram_id": demo_master_telegram_id,
                "demo_master_display_name": _DEFAULT_DEMO_MASTER_DISPLAY_NAME,
                "work_start": time(10, 0),
                "work_end": time(21, 0),
                "lunch_start": time(13, 0),
                "lunch_end": time(14, 0),
            },
        )

        conn.execute(
            text(
                """
                INSERT INTO services (code, label_ru, duration_minutes, is_active)
                VALUES (:code, :label_ru, :duration_minutes, true)
                ON CONFLICT (code) DO UPDATE
                    SET label_ru = EXCLUDED.label_ru,
                        duration_minutes = EXCLUDED.duration_minutes,
                        is_active = true
                """
            ),
            service_catalog,
        )


if __name__ == "__main__":
    run_seed(
        os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        bootstrap_master_telegram_id=resolve_bootstrap_master_telegram_id(
            os.getenv(BOOTSTRAP_MASTER_TELEGRAM_ID_ENV)
        ),
    )
