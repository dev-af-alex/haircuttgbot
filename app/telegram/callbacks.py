from __future__ import annotations

from dataclasses import dataclass
from re import compile as re_compile
from time import monotonic
from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.engine import Engine

from app.auth import RoleRepository, authorize_command
from app.auth.messages import RU_MESSAGES
from app.observability import emit_event

CALLBACK_DATA_MAX_LENGTH = 64
CALLBACK_PREFIX = "hb1"
_ALLOWED_ACTIONS = {"hm", "cm", "mm", "bk"}
_CONTEXT_PATTERN = re_compile(r"^[A-Za-z0-9_-]{1,32}$")

_ACTION_REQUIRED_COMMAND = {
    "cm": "client:book",
    "mm": "master:schedule",
}

_MENU_ROOT = "root"
_MENU_CLIENT = "client_menu"
_MENU_MASTER = "master_menu"

_MENU_ALLOWED_ACTIONS = {
    _MENU_ROOT: {"hm", "cm", "mm"},
    _MENU_CLIENT: {"hm", "bk"},
    _MENU_MASTER: {"hm", "bk"},
}

_ACTION_TARGET_MENU = {
    "hm": _MENU_ROOT,
    "cm": _MENU_CLIENT,
    "mm": _MENU_MASTER,
    "bk": _MENU_ROOT,
}

_MENU_TEXT = {
    _MENU_ROOT: "Главное меню. Выберите раздел.",
    _MENU_CLIENT: "Меню клиента. Выберите действие.",
    _MENU_MASTER: "Меню мастера. Выберите действие.",
}


@dataclass(frozen=True)
class CallbackPayload:
    version: str
    action: str
    context: str | None


@dataclass(frozen=True)
class CallbackHandleResult:
    text: str
    reply_markup: InlineKeyboardMarkup


@dataclass
class _UserMenuState:
    menu: str
    expires_at: float


class CallbackStateStore:
    def __init__(
        self,
        *,
        ttl_seconds: int = 900,
        now: Callable[[], float] = monotonic,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._now = now
        self._states: dict[int, _UserMenuState] = {}

    def current_menu(self, telegram_user_id: int) -> str:
        state = self._states.get(telegram_user_id)
        if state is None:
            return _MENU_ROOT
        if state.expires_at <= self._now():
            self._states.pop(telegram_user_id, None)
            return _MENU_ROOT
        return state.menu

    def set_menu(self, telegram_user_id: int, menu: str) -> None:
        self._states[telegram_user_id] = _UserMenuState(
            menu=menu,
            expires_at=self._now() + self._ttl_seconds,
        )

    def mark_stale(self, telegram_user_id: int, *, action: str) -> bool:
        menu = self.current_menu(telegram_user_id)
        allowed = _MENU_ALLOWED_ACTIONS.get(menu, _MENU_ALLOWED_ACTIONS[_MENU_ROOT])
        return action not in allowed


class TelegramCallbackRouter:
    def __init__(self, engine: Engine, *, state_store: CallbackStateStore | None = None) -> None:
        self._roles = RoleRepository(engine)
        self._state = state_store or CallbackStateStore()

    def seed_root_menu(self, telegram_user_id: int) -> None:
        self._state.set_menu(telegram_user_id, _MENU_ROOT)

    def handle(self, *, telegram_user_id: int, data: str | None) -> CallbackHandleResult:
        payload, error_code = decode_callback_data(data)
        if payload is None:
            emit_event(
                "telegram_callback_invalid",
                telegram_user_id=telegram_user_id,
                reason=error_code,
            )
            return self._invalid_response()

        role = self._roles.resolve_role(telegram_user_id)
        if role is None:
            emit_event(
                "rbac_deny",
                telegram_user_id=telegram_user_id,
                command=f"callback:{payload.action}",
                role=None,
                reason="unknown_user",
            )
            return CallbackHandleResult(
                text=RU_MESSAGES["unknown_user"],
                reply_markup=build_root_menu_markup(),
            )

        required_command = _ACTION_REQUIRED_COMMAND.get(payload.action)
        if required_command:
            decision = authorize_command(required_command, role)
            if not decision.allowed:
                emit_event(
                    "rbac_deny",
                    telegram_user_id=telegram_user_id,
                    command=f"callback:{payload.action}",
                    role=role,
                    reason="forbidden",
                )
                return CallbackHandleResult(
                    text=decision.message,
                    reply_markup=build_root_menu_markup(),
                )

        if self._state.mark_stale(telegram_user_id, action=payload.action):
            emit_event(
                "telegram_callback_stale",
                telegram_user_id=telegram_user_id,
                action=payload.action,
                menu=self._state.current_menu(telegram_user_id),
            )
            return self._stale_response()

        target_menu = _ACTION_TARGET_MENU[payload.action]
        self._state.set_menu(telegram_user_id, target_menu)
        return CallbackHandleResult(
            text=_MENU_TEXT[target_menu],
            reply_markup=build_menu_markup(target_menu),
        )

    def _invalid_response(self) -> CallbackHandleResult:
        return CallbackHandleResult(
            text=RU_MESSAGES["invalid_callback"],
            reply_markup=build_root_menu_markup(),
        )

    def _stale_response(self) -> CallbackHandleResult:
        return CallbackHandleResult(
            text=RU_MESSAGES["stale_callback"],
            reply_markup=build_root_menu_markup(),
        )


def encode_callback_data(*, action: str, context: str | None = None) -> str:
    if action not in _ALLOWED_ACTIONS:
        raise ValueError("Unsupported callback action.")
    parts = [CALLBACK_PREFIX, action]
    if context:
        if not _CONTEXT_PATTERN.match(context):
            raise ValueError("Invalid callback context.")
        parts.append(context)
    payload = "|".join(parts)
    if len(payload.encode("utf-8")) > CALLBACK_DATA_MAX_LENGTH:
        raise ValueError("Callback payload exceeds max length.")
    return payload


def decode_callback_data(data: str | None) -> tuple[CallbackPayload | None, str | None]:
    if data is None or not data.strip():
        return None, "empty"
    if len(data.encode("utf-8")) > CALLBACK_DATA_MAX_LENGTH:
        return None, "too_long"
    parts = data.split("|")
    if len(parts) not in {2, 3}:
        return None, "invalid_format"
    version, action = parts[0], parts[1]
    context = parts[2] if len(parts) == 3 else None
    if version != CALLBACK_PREFIX:
        return None, "unsupported_version"
    if action not in _ALLOWED_ACTIONS:
        return None, "unknown_action"
    if context is not None and not _CONTEXT_PATTERN.match(context):
        return None, "invalid_context"
    return CallbackPayload(version=version, action=action, context=context), None


def build_root_menu_markup() -> InlineKeyboardMarkup:
    return build_menu_markup(_MENU_ROOT)


def build_menu_markup(menu: str) -> InlineKeyboardMarkup:
    if menu == _MENU_CLIENT:
        rows = [
            [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action="bk"))],
            [InlineKeyboardButton(text="Главное меню", callback_data=encode_callback_data(action="hm"))],
        ]
    elif menu == _MENU_MASTER:
        rows = [
            [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action="bk"))],
            [InlineKeyboardButton(text="Главное меню", callback_data=encode_callback_data(action="hm"))],
        ]
    else:
        rows = [
            [
                InlineKeyboardButton(text="Клиент", callback_data=encode_callback_data(action="cm")),
                InlineKeyboardButton(text="Мастер", callback_data=encode_callback_data(action="mm")),
            ],
            [InlineKeyboardButton(text="Обновить", callback_data=encode_callback_data(action="hm"))],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
