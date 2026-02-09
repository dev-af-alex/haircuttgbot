from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from re import compile as re_compile
from time import monotonic
from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.auth import RoleRepository, authorize_command
from app.auth.messages import RU_MESSAGES
from app.booking import (
    BookingFlowRepository,
    SERVICE_OPTION_LABELS_RU,
    TelegramBookingFlowService,
)
from app.observability import emit_event

CALLBACK_DATA_MAX_LENGTH = 64
CALLBACK_PREFIX = "hb1"
_ALLOWED_ACTIONS = {
    "hm",
    "cm",
    "mm",
    "bk",
    "cb",
    "cc",
    "csm",
    "css",
    "csd",
    "csl",
    "ccf",
    "cci",
    "ccn",
}
_CONTEXT_PATTERN = re_compile(r"^[A-Za-z0-9_-]{1,32}$")
_SLOT_TOKEN_PATTERN = re_compile(r"^\d{12}$")
_DATE_TOKEN_PATTERN = re_compile(r"^\d{8}$")

_ACTION_REQUIRED_COMMAND = {
    "cm": "client:book",
    "mm": "master:schedule",
    "cb": "client:book",
    "csm": "client:book",
    "css": "client:book",
    "csd": "client:book",
    "csl": "client:book",
    "ccf": "client:book",
    "cc": "client:cancel",
    "cci": "client:cancel",
    "ccn": "client:cancel",
}

_MENU_ROOT = "root"
_MENU_CLIENT = "client_menu"
_MENU_MASTER = "master_menu"
_MENU_CLIENT_MASTER_SELECT = "client_master_select"
_MENU_CLIENT_SERVICE_SELECT = "client_service_select"
_MENU_CLIENT_DATE_SELECT = "client_date_select"
_MENU_CLIENT_SLOT_SELECT = "client_slot_select"
_MENU_CLIENT_CONFIRM = "client_confirm"
_MENU_CLIENT_CANCEL_SELECT = "client_cancel_select"
_MENU_CLIENT_CANCEL_CONFIRM = "client_cancel_confirm"

_MENU_ALLOWED_ACTIONS = {
    _MENU_ROOT: {"hm", "cm", "mm"},
    _MENU_CLIENT: {"hm", "bk", "cb", "cc"},
    _MENU_MASTER: {"hm", "bk"},
    _MENU_CLIENT_MASTER_SELECT: {"hm", "bk", "csm"},
    _MENU_CLIENT_SERVICE_SELECT: {"hm", "bk", "css"},
    _MENU_CLIENT_DATE_SELECT: {"hm", "bk", "csd"},
    _MENU_CLIENT_SLOT_SELECT: {"hm", "bk", "csl"},
    _MENU_CLIENT_CONFIRM: {"hm", "bk", "ccf"},
    _MENU_CLIENT_CANCEL_SELECT: {"hm", "bk", "cci"},
    _MENU_CLIENT_CANCEL_CONFIRM: {"hm", "bk", "ccn"},
}

_MENU_TEXT = {
    _MENU_ROOT: "Главное меню. Выберите раздел.",
    _MENU_CLIENT: "Меню клиента. Выберите действие.",
    _MENU_MASTER: "Меню мастера. Выберите действие.",
}

_ACTION_TARGET_MENU = {
    "hm": _MENU_ROOT,
    "cm": _MENU_CLIENT,
    "mm": _MENU_MASTER,
    "bk": _MENU_ROOT,
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
    notifications: list[dict[str, object]] = field(default_factory=list)


@dataclass
class _UserMenuState:
    menu: str
    expires_at: float
    context: dict[str, str]


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
        state = self._get_state(telegram_user_id)
        return state.menu if state is not None else _MENU_ROOT

    def set_menu(self, telegram_user_id: int, menu: str, *, reset_context: bool = False) -> None:
        context = {}
        state = self._get_state(telegram_user_id)
        if state is not None and not reset_context:
            context = dict(state.context)
        self._states[telegram_user_id] = _UserMenuState(
            menu=menu,
            expires_at=self._now() + self._ttl_seconds,
            context=context,
        )

    def set_context_value(self, telegram_user_id: int, key: str, value: str) -> None:
        state = self._get_state(telegram_user_id)
        if state is None:
            self.set_menu(telegram_user_id, _MENU_ROOT)
            state = self._states[telegram_user_id]
        state.context[key] = value
        state.expires_at = self._now() + self._ttl_seconds

    def get_context_value(self, telegram_user_id: int, key: str) -> str | None:
        state = self._get_state(telegram_user_id)
        if state is None:
            return None
        return state.context.get(key)

    def mark_stale(self, telegram_user_id: int, *, action: str) -> bool:
        menu = self.current_menu(telegram_user_id)
        allowed = _MENU_ALLOWED_ACTIONS.get(menu, _MENU_ALLOWED_ACTIONS[_MENU_ROOT])
        return action not in allowed

    def _get_state(self, telegram_user_id: int) -> _UserMenuState | None:
        state = self._states.get(telegram_user_id)
        if state is None:
            return None
        if state.expires_at <= self._now():
            self._states.pop(telegram_user_id, None)
            return None
        return state


class TelegramCallbackRouter:
    def __init__(self, engine: Engine, *, state_store: CallbackStateStore | None = None) -> None:
        self._engine = engine
        self._roles = RoleRepository(engine)
        self._flow = TelegramBookingFlowService(engine)
        self._flow_repo = BookingFlowRepository(engine)
        self._state = state_store or CallbackStateStore()

    def seed_root_menu(self, telegram_user_id: int) -> None:
        self._state.set_menu(telegram_user_id, _MENU_ROOT, reset_context=True)

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

        if payload.action in _ACTION_TARGET_MENU:
            return self._handle_static_menu_action(telegram_user_id=telegram_user_id, action=payload.action)
        if payload.action == "cb":
            return self._handle_client_start_booking(telegram_user_id=telegram_user_id)
        if payload.action == "csm":
            return self._handle_client_select_master(
                telegram_user_id=telegram_user_id,
                context=payload.context,
            )
        if payload.action == "css":
            return self._handle_client_select_service(
                telegram_user_id=telegram_user_id,
                context=payload.context,
            )
        if payload.action == "csd":
            return self._handle_client_select_date(
                telegram_user_id=telegram_user_id,
                context=payload.context,
            )
        if payload.action == "csl":
            return self._handle_client_select_slot(
                telegram_user_id=telegram_user_id,
                context=payload.context,
            )
        if payload.action == "ccf":
            return self._handle_client_confirm_booking(telegram_user_id=telegram_user_id)
        if payload.action == "cc":
            return self._handle_client_cancel_list(telegram_user_id=telegram_user_id)
        if payload.action == "cci":
            return self._handle_client_cancel_prepare(
                telegram_user_id=telegram_user_id,
                context=payload.context,
            )
        if payload.action == "ccn":
            return self._handle_client_cancel_confirm(
                telegram_user_id=telegram_user_id,
                context=payload.context,
            )
        return self._invalid_response()

    def _handle_static_menu_action(self, *, telegram_user_id: int, action: str) -> CallbackHandleResult:
        target_menu = _ACTION_TARGET_MENU[action]
        reset_context = target_menu == _MENU_ROOT
        self._state.set_menu(telegram_user_id, target_menu, reset_context=reset_context)
        return CallbackHandleResult(
            text=_MENU_TEXT[target_menu],
            reply_markup=build_menu_markup(target_menu),
        )

    def _handle_client_start_booking(self, *, telegram_user_id: int) -> CallbackHandleResult:
        response = self._flow.start()
        masters = response.get("masters", [])
        if not isinstance(masters, list) or not masters:
            self._state.set_menu(telegram_user_id, _MENU_CLIENT)
            return CallbackHandleResult(
                text="Нет доступных мастеров для записи.",
                reply_markup=build_menu_markup(_MENU_CLIENT),
            )

        self._state.set_menu(telegram_user_id, _MENU_CLIENT_MASTER_SELECT, reset_context=True)
        return CallbackHandleResult(
            text=str(response.get("message", "Выберите мастера.")),
            reply_markup=build_client_master_markup(masters),
        )

    def _handle_client_select_master(self, *, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None:
            return self._stale_response()
        try:
            master_id = int(context)
        except ValueError:
            return self._invalid_response()

        response = self._flow.select_master(master_id)
        service_options = response.get("service_options", [])
        if not isinstance(service_options, list) or not service_options:
            self._state.set_menu(telegram_user_id, _MENU_CLIENT_MASTER_SELECT)
            return CallbackHandleResult(
                text=str(response.get("message", "Мастер не найден.")),
                reply_markup=build_menu_markup(_MENU_CLIENT),
            )

        self._state.set_context_value(telegram_user_id, "master_id", str(master_id))
        self._state.set_menu(telegram_user_id, _MENU_CLIENT_SERVICE_SELECT)
        return CallbackHandleResult(
            text=str(response.get("message", "Выберите услугу.")),
            reply_markup=build_client_service_markup(service_options),
        )

    def _handle_client_select_service(self, *, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or context not in SERVICE_OPTION_LABELS_RU:
            return self._invalid_response()
        if self._state.get_context_value(telegram_user_id, "master_id") is None:
            return self._stale_response()

        self._state.set_context_value(telegram_user_id, "service_type", context)
        self._state.set_menu(telegram_user_id, _MENU_CLIENT_DATE_SELECT)
        return CallbackHandleResult(
            text="Выберите дату для записи.",
            reply_markup=build_client_date_markup(),
        )

    def _handle_client_select_date(self, *, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or not _DATE_TOKEN_PATTERN.match(context):
            return self._invalid_response()
        master_id_raw = self._state.get_context_value(telegram_user_id, "master_id")
        if master_id_raw is None:
            return self._stale_response()
        try:
            master_id = int(master_id_raw)
            on_date = datetime.strptime(context, "%Y%m%d").date()
        except ValueError:
            return self._invalid_response()

        response = self._flow.select_service(master_id=master_id, on_date=on_date)
        slots = response.get("slots", [])
        if not isinstance(slots, list) or not slots:
            self._state.set_menu(telegram_user_id, _MENU_CLIENT_DATE_SELECT)
            return CallbackHandleResult(
                text=f"{response.get('message', 'Выберите доступный слот.')}\nНа выбранную дату свободных слотов нет.",
                reply_markup=build_client_date_markup(),
            )

        self._state.set_menu(telegram_user_id, _MENU_CLIENT_SLOT_SELECT)
        return CallbackHandleResult(
            text=str(response.get("message", "Выберите доступный слот.")),
            reply_markup=build_client_slot_markup(slots),
        )

    def _handle_client_select_slot(self, *, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or not _SLOT_TOKEN_PATTERN.match(context):
            return self._invalid_response()
        master_id = self._state.get_context_value(telegram_user_id, "master_id")
        service_type = self._state.get_context_value(telegram_user_id, "service_type")
        if master_id is None or service_type is None:
            return self._stale_response()

        self._state.set_context_value(telegram_user_id, "slot_token", context)
        self._state.set_menu(telegram_user_id, _MENU_CLIENT_CONFIRM)
        slot_start = _parse_slot_token(context)
        summary = (
            "Подтвердите запись:\n"
            f"- Мастер ID: {master_id}\n"
            f"- Услуга: {SERVICE_OPTION_LABELS_RU.get(service_type, service_type)}\n"
            f"- Слот: {slot_start.isoformat()}"
        )
        return CallbackHandleResult(
            text=summary,
            reply_markup=build_client_confirm_markup(),
        )

    def _handle_client_confirm_booking(self, *, telegram_user_id: int) -> CallbackHandleResult:
        master_id_raw = self._state.get_context_value(telegram_user_id, "master_id")
        service_type = self._state.get_context_value(telegram_user_id, "service_type")
        slot_token = self._state.get_context_value(telegram_user_id, "slot_token")
        if master_id_raw is None or service_type is None or slot_token is None:
            return self._stale_response()

        try:
            master_id = int(master_id_raw)
            slot_start = _parse_slot_token(slot_token)
        except ValueError:
            return self._invalid_response()

        response = self._flow.confirm(
            client_telegram_user_id=telegram_user_id,
            master_id=master_id,
            service_type=service_type,
            slot_start=slot_start,
        )
        self._state.set_menu(telegram_user_id, _MENU_CLIENT, reset_context=True)
        return CallbackHandleResult(
            text=str(response.get("message", "")),
            reply_markup=build_menu_markup(_MENU_CLIENT),
            notifications=_coerce_notifications(response.get("notifications")),
        )

    def _handle_client_cancel_list(self, *, telegram_user_id: int) -> CallbackHandleResult:
        bookings = self._list_client_future_bookings(telegram_user_id=telegram_user_id)
        if not bookings:
            self._state.set_menu(telegram_user_id, _MENU_CLIENT)
            return CallbackHandleResult(
                text="Активных будущих записей для отмены нет.",
                reply_markup=build_menu_markup(_MENU_CLIENT),
            )

        self._state.set_menu(telegram_user_id, _MENU_CLIENT_CANCEL_SELECT)
        return CallbackHandleResult(
            text="Выберите запись для отмены.",
            reply_markup=build_client_cancel_select_markup(bookings),
        )

    def _handle_client_cancel_prepare(self, *, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None:
            return self._invalid_response()
        try:
            booking_id = int(context)
        except ValueError:
            return self._invalid_response()

        self._state.set_context_value(telegram_user_id, "cancel_booking_id", str(booking_id))
        self._state.set_menu(telegram_user_id, _MENU_CLIENT_CANCEL_CONFIRM)
        return CallbackHandleResult(
            text=f"Подтвердите отмену записи #{booking_id}.",
            reply_markup=build_client_cancel_confirm_markup(booking_id=booking_id),
        )

    def _handle_client_cancel_confirm(self, *, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        booking_id_raw = context or self._state.get_context_value(telegram_user_id, "cancel_booking_id")
        if booking_id_raw is None:
            return self._stale_response()
        try:
            booking_id = int(booking_id_raw)
        except ValueError:
            return self._invalid_response()

        response = self._flow.cancel(
            client_telegram_user_id=telegram_user_id,
            booking_id=booking_id,
        )
        self._state.set_menu(telegram_user_id, _MENU_CLIENT, reset_context=True)
        return CallbackHandleResult(
            text=str(response.get("message", "")),
            reply_markup=build_menu_markup(_MENU_CLIENT),
            notifications=_coerce_notifications(response.get("notifications")),
        )

    def _list_client_future_bookings(self, *, telegram_user_id: int) -> list[dict[str, object]]:
        client_user_id = self._flow_repo.resolve_client_user_id(telegram_user_id)
        if client_user_id is None:
            return []

        now_utc = datetime.now(UTC)
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT b.id, b.slot_start, b.service_type, m.display_name
                    FROM bookings b
                    JOIN masters m ON m.id = b.master_id
                    WHERE b.client_user_id = :client_user_id
                      AND b.status = 'active'
                      AND b.slot_start >= :now_utc
                    ORDER BY b.slot_start
                    """
                ),
                {"client_user_id": client_user_id, "now_utc": now_utc},
            ).mappings()
            result: list[dict[str, object]] = []
            for row in rows:
                slot_start_raw = row["slot_start"]
                if isinstance(slot_start_raw, datetime):
                    slot_start = slot_start_raw
                else:
                    slot_start = datetime.fromisoformat(str(slot_start_raw))
                result.append(
                    {
                        "id": int(row["id"]),
                        "slot_start": slot_start,
                        "service_type": str(row["service_type"]),
                        "master_name": str(row["display_name"]),
                    }
                )
            return result

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


def _parse_slot_token(token: str) -> datetime:
    if not _SLOT_TOKEN_PATTERN.match(token):
        raise ValueError("Invalid slot token")
    parsed = datetime.strptime(token, "%Y%m%d%H%M")
    return parsed.replace(tzinfo=UTC)


def _format_slot_token(slot_start: datetime) -> str:
    return slot_start.astimezone(UTC).strftime("%Y%m%d%H%M")


def build_root_menu_markup() -> InlineKeyboardMarkup:
    return build_menu_markup(_MENU_ROOT)


def build_menu_markup(menu: str) -> InlineKeyboardMarkup:
    if menu == _MENU_CLIENT:
        rows = [
            [InlineKeyboardButton(text="Новая запись", callback_data=encode_callback_data(action="cb"))],
            [InlineKeyboardButton(text="Отменить запись", callback_data=encode_callback_data(action="cc"))],
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


def build_client_master_markup(masters: list[object]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for item in masters:
        if not isinstance(item, dict):
            continue
        master_id = item.get("id")
        name = item.get("display_name")
        if not isinstance(master_id, int) or not isinstance(name, str):
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=name,
                    callback_data=encode_callback_data(action="csm", context=str(master_id)),
                )
            ]
        )
    rows.extend(
        [
            [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action="bk"))],
            [InlineKeyboardButton(text="Главное меню", callback_data=encode_callback_data(action="hm"))],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_client_service_markup(service_options: list[object]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for item in service_options:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        label = item.get("label")
        if not isinstance(code, str) or not isinstance(label, str):
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=encode_callback_data(action="css", context=code),
                )
            ]
        )
    rows.extend(
        [
            [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action="bk"))],
            [InlineKeyboardButton(text="Главное меню", callback_data=encode_callback_data(action="hm"))],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_client_date_markup(*, days_ahead: int = 7) -> InlineKeyboardMarkup:
    today = datetime.now(UTC).date()
    rows: list[list[InlineKeyboardButton]] = []
    for offset in range(days_ahead):
        day = today + timedelta(days=offset)
        token = day.strftime("%Y%m%d")
        rows.append(
            [
                InlineKeyboardButton(
                    text=day.isoformat(),
                    callback_data=encode_callback_data(action="csd", context=token),
                )
            ]
        )
    rows.extend(
        [
            [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action="bk"))],
            [InlineKeyboardButton(text="Главное меню", callback_data=encode_callback_data(action="hm"))],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_client_slot_markup(slots: list[object]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for item in slots:
        if not isinstance(item, dict):
            continue
        start_at = item.get("start_at")
        if not isinstance(start_at, str):
            continue
        slot_start = datetime.fromisoformat(start_at)
        token = _format_slot_token(slot_start)
        rows.append(
            [
                InlineKeyboardButton(
                    text=slot_start.astimezone(UTC).strftime("%H:%M"),
                    callback_data=encode_callback_data(action="csl", context=token),
                )
            ]
        )
    rows.extend(
        [
            [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action="bk"))],
            [InlineKeyboardButton(text="Главное меню", callback_data=encode_callback_data(action="hm"))],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_client_confirm_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data=encode_callback_data(action="ccf"))],
            [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action="bk"))],
            [InlineKeyboardButton(text="Главное меню", callback_data=encode_callback_data(action="hm"))],
        ]
    )


def build_client_cancel_select_markup(bookings: list[dict[str, object]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for booking in bookings:
        booking_id = booking.get("id")
        slot_start = booking.get("slot_start")
        master_name = booking.get("master_name")
        if not isinstance(booking_id, int) or not isinstance(slot_start, datetime) or not isinstance(master_name, str):
            continue
        label = f"#{booking_id} {slot_start.astimezone(UTC).strftime('%Y-%m-%d %H:%M')} {master_name}"
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=encode_callback_data(action="cci", context=str(booking_id)),
                )
            ]
        )
    rows.extend(
        [
            [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action="bk"))],
            [InlineKeyboardButton(text="Главное меню", callback_data=encode_callback_data(action="hm"))],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_client_cancel_confirm_markup(*, booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Отменить #{booking_id}",
                    callback_data=encode_callback_data(action="ccn", context=str(booking_id)),
                )
            ],
            [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action="bk"))],
            [InlineKeyboardButton(text="Главное меню", callback_data=encode_callback_data(action="hm"))],
        ]
    )


def _coerce_notifications(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    notifications: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        recipient = item.get("recipient_telegram_user_id")
        message = item.get("message")
        if not isinstance(recipient, int) or not isinstance(message, str):
            continue
        notifications.append(
            {
                "recipient_telegram_user_id": recipient,
                "message": message,
            }
        )
    return notifications
