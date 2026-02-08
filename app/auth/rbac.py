from __future__ import annotations

from app.auth.messages import RU_MESSAGES

COMMAND_ROLE_MAP = {
    "client:book": "Client",
    "client:cancel": "Client",
    "master:schedule": "Master",
    "master:day-off": "Master",
    "master:lunch": "Master",
}


class RbacResult:
    def __init__(self, allowed: bool, message: str) -> None:
        self.allowed = allowed
        self.message = message


def authorize_command(command: str, role: str | None) -> RbacResult:
    required_role = COMMAND_ROLE_MAP.get(command)

    if role is None:
        return RbacResult(False, RU_MESSAGES["unknown_user"])

    if required_role is None:
        return RbacResult(True, RU_MESSAGES["allowed"])

    if role != required_role:
        return RbacResult(False, RU_MESSAGES["forbidden"])

    return RbacResult(True, RU_MESSAGES["allowed"])
