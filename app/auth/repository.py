from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine


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
