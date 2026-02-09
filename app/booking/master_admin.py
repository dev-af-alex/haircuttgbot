from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import time

from sqlalchemy import text
from sqlalchemy.engine import Engine

_MASTER_WORK_START = time(10, 0)
_MASTER_WORK_END = time(21, 0)
_MASTER_LUNCH_START = time(13, 0)
_MASTER_LUNCH_END = time(14, 0)
_TELEGRAM_NICKNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{5,32}$")


@dataclass(frozen=True)
class MasterAdminResult:
    applied: bool
    message: str
    target_telegram_user_id: int | None
    reason: str | None = None


class MasterAdminService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_promotable_users(self, *, limit: int = 20) -> list[dict[str, object]]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT u.telegram_user_id
                    FROM users u
                    LEFT JOIN roles r ON r.id = u.role_id
                    LEFT JOIN masters m ON m.user_id = u.id AND m.is_active = true
                    WHERE m.id IS NULL
                      AND (r.name IS NULL OR r.name <> 'Master')
                    ORDER BY u.telegram_user_id
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            ).mappings()
            return [{"telegram_user_id": int(row["telegram_user_id"])} for row in rows]

    def list_removable_masters(
        self,
        *,
        bootstrap_master_telegram_user_id: int,
        limit: int = 20,
    ) -> list[dict[str, object]]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT u.telegram_user_id, m.display_name
                    FROM masters m
                    JOIN users u ON u.id = m.user_id
                    WHERE m.is_active = true
                      AND u.telegram_user_id <> :bootstrap_master_telegram_user_id
                    ORDER BY u.telegram_user_id
                    LIMIT :limit
                    """
                ),
                {
                    "bootstrap_master_telegram_user_id": bootstrap_master_telegram_user_id,
                    "limit": limit,
                },
            ).mappings()
            return [
                {
                    "telegram_user_id": int(row["telegram_user_id"]),
                    "display_name": str(row["display_name"]),
                }
                for row in rows
            ]

    def add_master(self, *, telegram_user_id: int) -> MasterAdminResult:
        with self._engine.begin() as conn:
            master_role_id = conn.execute(text("SELECT id FROM roles WHERE name = 'Master'")).scalar_one_or_none()
            if master_role_id is None:
                return MasterAdminResult(
                    applied=False,
                    message="Роль Master не найдена. Выполните миграции и seed.",
                    target_telegram_user_id=telegram_user_id,
                    reason="master_role_missing",
                )

            user = conn.execute(
                text(
                    """
                    SELECT id, role_id
                    FROM users
                    WHERE telegram_user_id = :telegram_user_id
                    """
                ),
                {"telegram_user_id": telegram_user_id},
            ).mappings().first()

            if user is None:
                user_id = int(
                    conn.execute(
                        text(
                            """
                            INSERT INTO users (telegram_user_id, role_id)
                            VALUES (:telegram_user_id, :master_role_id)
                            RETURNING id
                            """
                        ),
                        {
                            "telegram_user_id": telegram_user_id,
                            "master_role_id": master_role_id,
                        },
                    ).scalar_one()
                )
            else:
                user_id = int(user["id"])
                if int(user["role_id"]) != int(master_role_id):
                    conn.execute(
                        text(
                            """
                            UPDATE users
                            SET role_id = :master_role_id
                            WHERE id = :user_id
                            """
                        ),
                        {
                            "master_role_id": master_role_id,
                            "user_id": user_id,
                        },
                    )

            master = conn.execute(
                text(
                    """
                    SELECT id, is_active
                    FROM masters
                    WHERE user_id = :user_id
                    """
                ),
                {"user_id": user_id},
            ).mappings().first()

            if master is None:
                conn.execute(
                    text(
                        """
                        INSERT INTO masters (user_id, display_name, work_start, work_end, lunch_start, lunch_end, is_active)
                        VALUES (
                            :user_id,
                            :display_name,
                            :work_start,
                            :work_end,
                            :lunch_start,
                            :lunch_end,
                            true
                        )
                        """
                    ),
                    {
                        "user_id": user_id,
                        "display_name": f"Master {telegram_user_id}",
                        "work_start": _MASTER_WORK_START,
                        "work_end": _MASTER_WORK_END,
                        "lunch_start": _MASTER_LUNCH_START,
                        "lunch_end": _MASTER_LUNCH_END,
                    },
                )
                return MasterAdminResult(
                    applied=True,
                    message=f"Мастер {telegram_user_id} добавлен.",
                    target_telegram_user_id=telegram_user_id,
                    reason="added",
                )

            if bool(master["is_active"]):
                return MasterAdminResult(
                    applied=True,
                    message=f"Мастер {telegram_user_id} уже активен.",
                    target_telegram_user_id=telegram_user_id,
                    reason="already_active",
                )

            conn.execute(
                text(
                    """
                    UPDATE masters
                    SET is_active = true
                    WHERE id = :master_id
                    """
                ),
                {"master_id": int(master["id"])}
            )
            return MasterAdminResult(
                applied=True,
                message=f"Мастер {telegram_user_id} добавлен.",
                target_telegram_user_id=telegram_user_id,
                reason="reactivated",
            )

    def add_master_by_nickname(self, *, raw_nickname: str) -> MasterAdminResult:
        normalized_nickname = normalize_telegram_nickname(raw_nickname)
        if normalized_nickname is None:
            return MasterAdminResult(
                applied=False,
                message="Неверный формат nickname. Используйте @nickname (латиница, цифры, подчёркивание).",
                target_telegram_user_id=None,
                reason="invalid_nickname_format",
            )

        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT telegram_user_id
                    FROM users
                    WHERE telegram_username IS NOT NULL
                      AND lower(telegram_username) = :normalized_nickname
                    ORDER BY telegram_user_id
                    LIMIT 2
                    """
                ),
                {"normalized_nickname": normalized_nickname},
            ).all()

        if not rows:
            return MasterAdminResult(
                applied=False,
                message=f"Пользователь с nickname @{normalized_nickname} не найден.",
                target_telegram_user_id=None,
                reason="nickname_not_found",
            )

        if len(rows) > 1:
            return MasterAdminResult(
                applied=False,
                message=f"Nickname @{normalized_nickname} неоднозначен. Обратитесь к администратору.",
                target_telegram_user_id=None,
                reason="nickname_ambiguous",
            )

        target_telegram_user_id = int(rows[0][0])
        base_result = self.add_master(telegram_user_id=target_telegram_user_id)
        return MasterAdminResult(
            applied=base_result.applied,
            message=f"{base_result.message} (nickname: @{normalized_nickname})",
            target_telegram_user_id=target_telegram_user_id,
            reason=base_result.reason,
        )

    def remove_master(
        self,
        *,
        telegram_user_id: int,
        bootstrap_master_telegram_user_id: int,
    ) -> MasterAdminResult:
        if telegram_user_id == bootstrap_master_telegram_user_id:
            return MasterAdminResult(
                applied=False,
                message="Нельзя удалить bootstrap-мастера.",
                target_telegram_user_id=telegram_user_id,
                reason="bootstrap_blocked",
            )

        with self._engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT m.id AS master_id, m.is_active
                    FROM users u
                    JOIN masters m ON m.user_id = u.id
                    WHERE u.telegram_user_id = :telegram_user_id
                    """
                ),
                {"telegram_user_id": telegram_user_id},
            ).mappings().first()

            if row is None:
                return MasterAdminResult(
                    applied=False,
                    message="Мастер не найден.",
                    target_telegram_user_id=telegram_user_id,
                    reason="master_not_found",
                )

            if not bool(row["is_active"]):
                return MasterAdminResult(
                    applied=True,
                    message=f"Мастер {telegram_user_id} уже неактивен.",
                    target_telegram_user_id=telegram_user_id,
                    reason="already_inactive",
                )

            conn.execute(
                text(
                    """
                    UPDATE masters
                    SET is_active = false
                    WHERE id = :master_id
                    """
                ),
                {"master_id": int(row["master_id"])}
            )
            return MasterAdminResult(
                applied=True,
                message=f"Мастер {telegram_user_id} удален из активных.",
                target_telegram_user_id=telegram_user_id,
                reason="deactivated",
            )


def normalize_telegram_nickname(raw_nickname: str | None) -> str | None:
    candidate = (raw_nickname or "").strip()
    if not candidate.startswith("@"):
        return None

    body = candidate[1:].strip()
    if not _TELEGRAM_NICKNAME_PATTERN.fullmatch(body):
        return None
    return body.lower()
