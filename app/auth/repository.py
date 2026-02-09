from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.engine import Engine

_TELEGRAM_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{5,32}$")


class RoleRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def resolve_role(self, telegram_user_id: int) -> str | None:
        query = text(
            """
            SELECT r.name
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE u.telegram_user_id = :telegram_user_id
            """
        )
        with self._engine.connect() as conn:
            row = conn.execute(query, {"telegram_user_id": telegram_user_id}).first()
            return row[0] if row else None

    def resolve_or_register_role_for_start(
        self,
        *,
        telegram_user_id: int,
        telegram_username: str | None,
    ) -> str | None:
        normalized_username = normalize_telegram_username(telegram_username)
        with self._engine.begin() as conn:
            self._ensure_client_role(conn)
            conn.execute(
                text(
                    """
                    INSERT INTO users (telegram_user_id, telegram_username, role_id)
                    VALUES (
                        :telegram_user_id,
                        :telegram_username,
                        (SELECT id FROM roles WHERE name = 'Client')
                    )
                    ON CONFLICT (telegram_user_id) DO UPDATE
                    SET telegram_username = COALESCE(users.telegram_username, EXCLUDED.telegram_username)
                    """
                ),
                {
                    "telegram_user_id": telegram_user_id,
                    "telegram_username": normalized_username,
                },
            )
            row = conn.execute(
                text(
                    """
                    SELECT r.name
                    FROM users u
                    JOIN roles r ON r.id = u.role_id
                    WHERE u.telegram_user_id = :telegram_user_id
                    """
                ),
                {"telegram_user_id": telegram_user_id},
            ).first()
            return row[0] if row else None

    @staticmethod
    def _ensure_client_role(conn: Connection) -> None:
        conn.execute(
            text(
                """
                INSERT INTO roles (name)
                VALUES ('Client')
                ON CONFLICT (name) DO NOTHING
                """
            )
        )


def normalize_telegram_username(raw_username: str | None) -> str | None:
    candidate = (raw_username or "").strip()
    if not candidate:
        return None
    if candidate.startswith("@"):
        candidate = candidate[1:].strip()
    if not _TELEGRAM_USERNAME_PATTERN.fullmatch(candidate):
        return None
    return candidate.lower()
