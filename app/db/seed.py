from __future__ import annotations

import os
from datetime import time

from sqlalchemy import create_engine, text

DEFAULT_DATABASE_URL = "postgresql+psycopg2://haircuttgbot:haircuttgbot@postgres:5432/haircuttgbot"


def run_seed(database_url: str) -> None:
    engine = create_engine(database_url, future=True)

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
                INSERT INTO users (telegram_user_id, role_id)
                VALUES
                    (1000001, (SELECT id FROM roles WHERE name = 'Master')),
                    (1000002, (SELECT id FROM roles WHERE name = 'Master'))
                ON CONFLICT (telegram_user_id) DO NOTHING
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT INTO masters (user_id, display_name, work_start, work_end, lunch_start, lunch_end, is_active)
                VALUES
                    ((SELECT id FROM users WHERE telegram_user_id = 1000001), 'Master Demo 1', :work_start, :work_end, :lunch_start, :lunch_end, true),
                    ((SELECT id FROM users WHERE telegram_user_id = 1000002), 'Master Demo 2', :work_start, :work_end, :lunch_start, :lunch_end, true)
                ON CONFLICT (user_id) DO NOTHING
                """
            ),
            {
                "work_start": time(10, 0),
                "work_end": time(21, 0),
                "lunch_start": time(13, 0),
                "lunch_end": time(14, 0),
            },
        )


if __name__ == "__main__":
    run_seed(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
