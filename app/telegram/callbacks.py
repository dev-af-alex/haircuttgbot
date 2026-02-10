from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time as dt_time, timedelta
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
    MasterAdminService,
    MasterDayOffCommand,
    MasterLunchBreakCommand,
    MasterManualBookingCommand,
    MasterScheduleService,
    SERVICE_OPTION_LABELS_RU,
    TelegramBookingFlowService,
    list_service_options,
    resolve_service_duration_minutes,
)
from app.db.seed import BOOTSTRAP_MASTER_TELEGRAM_ID_ENV, resolve_bootstrap_master_telegram_id
from app.observability import emit_event, observe_master_admin_outcome
from app.timezone import (
    business_day_bounds,
    business_now,
    combine_business_date_time,
    normalize_utc,
    utc_now,
)
from app.telegram.presentation import (
    MOBILE_DATE_SLOT_MAX_BUTTONS_PER_ROW,
    MOBILE_MENU_MAX_BUTTONS_PER_ROW,
    chunk_inline_buttons,
    format_ru_date,
    format_ru_datetime,
    format_ru_slot_range,
    format_ru_time,
)

CALLBACK_DATA_MAX_LENGTH = 64
CALLBACK_PREFIX = "hb1"
BOOKING_DATE_HORIZON_DAYS = 60
BOOKING_DATE_PAGE_SIZE = 7
_MASTER_CANCEL_REASONS = {
    "busy": "Плотная загрузка мастера.",
    "sick": "Мастер заболел.",
    "personal": "Личные обстоятельства.",
}
_MASTER_LUNCH_PRESETS = {
    "p13": ("13:00:00", "14:00:00"),
    "p14": ("14:00:00", "15:00:00"),
    "p18": ("18:00:00", "19:00:00"),
}
_MASTER_ADMIN_LIMIT = 20

_ALLOWED_ACTIONS = {
    "hm",
    "cm",
    "mm",
    "mr",
    "bk",
    "cb",
    "cc",
    "csm",
    "css",
    "csd",
    "cdp",
    "csl",
    "ccf",
    "cci",
    "ccn",
    "msv",
    "msd",
    "msu",
    "mlm",
    "mls",
    "msb",
    "mbs",
    "mbd",
    "mbp",
    "mbl",
    "mbc",
    "msc",
    "mci",
    "mcr",
    "mcn",
    "mam",
    "maa",
    "mau",
    "mad",
    "mar",
    "man",
    "max",
}
_CONTEXT_PATTERN = re_compile(r"^[A-Za-z0-9_-]{1,32}$")
_SLOT_TOKEN_PATTERN = re_compile(r"^\d{12}$")
_DATE_TOKEN_PATTERN = re_compile(r"^\d{8}$")
_PAGE_TOKEN_PATTERN = re_compile(r"^p\d{1,2}$")

_ACTION_REQUIRED_COMMAND = {
    "cm": "client:book",
    "cb": "client:book",
    "csm": "client:book",
    "css": "client:book",
    "csd": "client:book",
    "cdp": "client:book",
    "csl": "client:book",
    "ccf": "client:book",
    "cc": "client:cancel",
    "cci": "client:cancel",
    "ccn": "client:cancel",
    "mm": "master:schedule",
    "mr": "master:schedule",
    "msv": "master:schedule",
    "msd": "master:day-off",
    "msu": "master:day-off",
    "mlm": "master:lunch",
    "mls": "master:lunch",
    "msb": "master:schedule",
    "mbs": "master:schedule",
    "mbd": "master:schedule",
    "mbp": "master:schedule",
    "mbl": "master:schedule",
    "mbc": "master:schedule",
    "msc": "master:schedule",
    "mci": "master:schedule",
    "mcr": "master:schedule",
    "mcn": "master:schedule",
    "mam": "master:schedule",
    "maa": "master:schedule",
    "mau": "master:schedule",
    "mad": "master:schedule",
    "mar": "master:schedule",
    "man": "master:schedule",
    "max": "master:schedule",
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

_MENU_MASTER_SCHEDULE_DATE_SELECT = "master_schedule_date_select"
_MENU_MASTER_DAY_OFF_SELECT = "master_day_off_select"
_MENU_MASTER_LUNCH_SELECT = "master_lunch_select"
_MENU_MASTER_MANUAL_SERVICE_SELECT = "master_manual_service_select"
_MENU_MASTER_MANUAL_DATE_SELECT = "master_manual_date_select"
_MENU_MASTER_MANUAL_SLOT_SELECT = "master_manual_slot_select"
_MENU_MASTER_MANUAL_CLIENT_INPUT = "master_manual_client_input"
_MENU_MASTER_MANUAL_CONFIRM = "master_manual_confirm"
_MENU_MASTER_CANCEL_SELECT = "master_cancel_select"
_MENU_MASTER_CANCEL_REASON_SELECT = "master_cancel_reason_select"
_MENU_MASTER_CANCEL_CONFIRM = "master_cancel_confirm"
_MENU_MASTER_ADMIN = "master_admin_menu"
_MENU_MASTER_ADMIN_ADD_SELECT = "master_admin_add_select"
_MENU_MASTER_ADMIN_REMOVE_SELECT = "master_admin_remove_select"
_MENU_MASTER_ADMIN_ADD_NICKNAME_INPUT = "master_admin_add_nickname_input"
_MENU_MASTER_ADMIN_RENAME_SELECT = "master_admin_rename_select"
_MENU_MASTER_ADMIN_RENAME_INPUT = "master_admin_rename_input"

_MENU_ALLOWED_ACTIONS = {
    _MENU_ROOT: {"hm", "cm", "mm"},
    _MENU_CLIENT: {"hm", "bk", "cb", "cc"},
    _MENU_MASTER: {"hm", "bk", "msv", "msd", "mlm", "msb", "msc", "mam"},
    _MENU_CLIENT_MASTER_SELECT: {"hm", "bk", "csm"},
    _MENU_CLIENT_SERVICE_SELECT: {"hm", "bk", "css"},
    _MENU_CLIENT_DATE_SELECT: {"hm", "bk", "csd", "cdp"},
    _MENU_CLIENT_SLOT_SELECT: {"hm", "bk", "csl"},
    _MENU_CLIENT_CONFIRM: {"hm", "bk", "ccf"},
    _MENU_CLIENT_CANCEL_SELECT: {"hm", "bk", "cci"},
    _MENU_CLIENT_CANCEL_CONFIRM: {"hm", "bk", "ccn"},
    _MENU_MASTER_SCHEDULE_DATE_SELECT: {"hm", "mr", "msv"},
    _MENU_MASTER_DAY_OFF_SELECT: {"hm", "mr", "msu"},
    _MENU_MASTER_LUNCH_SELECT: {"hm", "mr", "mls"},
    _MENU_MASTER_MANUAL_SERVICE_SELECT: {"hm", "mr", "mbs"},
    _MENU_MASTER_MANUAL_DATE_SELECT: {"hm", "mr", "mbd", "mbp"},
    _MENU_MASTER_MANUAL_SLOT_SELECT: {"hm", "mr", "mbl"},
    _MENU_MASTER_MANUAL_CLIENT_INPUT: {"hm", "mr"},
    _MENU_MASTER_MANUAL_CONFIRM: {"hm", "mr", "mbc"},
    _MENU_MASTER_CANCEL_SELECT: {"hm", "mr", "mci"},
    _MENU_MASTER_CANCEL_REASON_SELECT: {"hm", "mr", "mcr"},
    _MENU_MASTER_CANCEL_CONFIRM: {"hm", "mr", "mcn"},
    _MENU_MASTER_ADMIN: {"hm", "mr", "maa", "mad", "man"},
    _MENU_MASTER_ADMIN_ADD_SELECT: {"hm", "mr"},
    _MENU_MASTER_ADMIN_ADD_NICKNAME_INPUT: {"hm", "mr"},
    _MENU_MASTER_ADMIN_REMOVE_SELECT: {"hm", "mr", "mar"},
    _MENU_MASTER_ADMIN_RENAME_SELECT: {"hm", "mr", "max"},
    _MENU_MASTER_ADMIN_RENAME_INPUT: {"hm", "mr"},
}

_MENU_TEXT = {
    _MENU_ROOT: "Выберите раздел.",
    _MENU_CLIENT: "Меню клиента. Выберите действие.",
    _MENU_MASTER: "Меню мастера. Выберите действие.",
    _MENU_MASTER_ADMIN: "Управление мастерами. Выберите действие.",
}
_START_GREETING = "Добро пожаловать в барбершоп."
_MASTER_DISPLAY_NAME_FALLBACK = "Мастер (имя не указано)"
_MASTER_ADMIN_ADD_NICKNAME_PROMPT = (
    "Введите nickname пользователя для назначения мастером (формат: @nickname)."
)
_MASTER_ADMIN_RENAME_PROMPT = "Введите новое имя мастера (1-64 символа)."
_MASTER_MANUAL_CLIENT_PROMPT = "Введите клиента для ручной записи (любой текст, до 160 символов)."

_ACTION_TARGET_MENU = {
    "hm": _MENU_ROOT,
    "cm": _MENU_CLIENT,
    "mm": _MENU_MASTER,
    "mr": _MENU_MASTER,
    "mam": _MENU_MASTER_ADMIN,
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
    def __init__(
        self,
        engine: Engine,
        *,
        state_store: CallbackStateStore | None = None,
        bootstrap_master_telegram_user_id: int | None = None,
    ) -> None:
        self._engine = engine
        self._roles = RoleRepository(engine)
        self._flow = TelegramBookingFlowService(engine)
        self._flow_repo = BookingFlowRepository(engine)
        self._schedule = MasterScheduleService(engine)
        self._master_admin = MasterAdminService(engine)
        self._bootstrap_master_telegram_user_id = (
            bootstrap_master_telegram_user_id
            if bootstrap_master_telegram_user_id is not None
            else self._resolve_bootstrap_telegram_user_id()
        )
        self._state = state_store or CallbackStateStore()

    @staticmethod
    def _resolve_bootstrap_telegram_user_id() -> int:
        raw_value = os.getenv(BOOTSTRAP_MASTER_TELEGRAM_ID_ENV, "1000001")
        return resolve_bootstrap_master_telegram_id(raw_value)

    def seed_root_menu(self, telegram_user_id: int) -> None:
        self._state.set_menu(telegram_user_id, _MENU_ROOT, reset_context=True)

    def start_menu(
        self,
        *,
        telegram_user_id: int,
        telegram_username: str | None = None,
    ) -> CallbackHandleResult:
        role = self._roles.resolve_or_register_role_for_start(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
        )
        if role == "Client":
            self._state.set_menu(telegram_user_id, _MENU_CLIENT, reset_context=True)
            return CallbackHandleResult(
                text=f"{_START_GREETING}\n{_MENU_TEXT[_MENU_CLIENT]}",
                reply_markup=build_menu_markup(_MENU_CLIENT),
            )
        if role == "Master":
            self._state.set_menu(telegram_user_id, _MENU_MASTER, reset_context=True)
            return CallbackHandleResult(
                text=f"{_START_GREETING}\n{_MENU_TEXT[_MENU_MASTER]}",
                reply_markup=build_menu_markup(_MENU_MASTER),
            )
        self._state.set_menu(telegram_user_id, _MENU_ROOT, reset_context=True)
        return CallbackHandleResult(
            text=RU_MESSAGES["unknown_user"],
            reply_markup=build_root_menu_markup(),
        )

    def handle(self, *, telegram_user_id: int, data: str | None) -> CallbackHandleResult:
        payload, error_code = decode_callback_data(data)
        if payload is None:
            emit_event(
                "telegram_callback_invalid",
                telegram_user_id=telegram_user_id,
                reason=error_code,
            )
            return self._invalid_response(telegram_user_id=telegram_user_id)

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
                    reply_markup=self._default_markup_for_role(role),
                )

        if payload.action in {"mam", "maa", "mau", "mad", "mar", "man", "max"} and not self._is_bootstrap_master(
            telegram_user_id=telegram_user_id
        ):
            observe_master_admin_outcome("rbac", "denied")
            emit_event(
                "master_admin_action",
                actor_telegram_user_id=telegram_user_id,
                target_telegram_user_id=None,
                action="rbac",
                outcome="denied",
                reason="bootstrap_only",
            )
            emit_event(
                "rbac_deny",
                telegram_user_id=telegram_user_id,
                command=f"callback:{payload.action}",
                role=role,
                reason="bootstrap_only",
            )
            return CallbackHandleResult(
                text=RU_MESSAGES["forbidden"],
                reply_markup=build_menu_markup(_MENU_MASTER),
            )

        if self._state.mark_stale(telegram_user_id, action=payload.action):
            emit_event(
                "telegram_callback_stale",
                telegram_user_id=telegram_user_id,
                action=payload.action,
                menu=self._state.current_menu(telegram_user_id),
            )
            return self._stale_response(telegram_user_id=telegram_user_id)

        if payload.action in _ACTION_TARGET_MENU:
            return self._handle_static_menu_action(telegram_user_id=telegram_user_id, action=payload.action)

        handlers: dict[str, Callable[[int, str | None], CallbackHandleResult]] = {
            "cb": lambda user_id, _: self._handle_client_start_booking(telegram_user_id=user_id),
            "csm": self._handle_client_select_master,
            "css": self._handle_client_select_service,
            "cdp": self._handle_client_date_page,
            "csd": self._handle_client_select_date,
            "csl": self._handle_client_select_slot,
            "ccf": lambda user_id, _: self._handle_client_confirm_booking(telegram_user_id=user_id),
            "cc": lambda user_id, _: self._handle_client_cancel_list(telegram_user_id=user_id),
            "cci": self._handle_client_cancel_prepare,
            "ccn": self._handle_client_cancel_confirm,
            "msv": self._handle_master_view_schedule,
            "msd": lambda user_id, _: self._handle_master_day_off_start(telegram_user_id=user_id),
            "msu": self._handle_master_day_off_apply,
            "mlm": lambda user_id, _: self._handle_master_lunch_start(telegram_user_id=user_id),
            "mls": self._handle_master_lunch_apply,
            "msb": lambda user_id, _: self._handle_master_manual_start(telegram_user_id=user_id),
            "mbs": self._handle_master_manual_select_service,
            "mbp": self._handle_master_manual_date_page,
            "mbd": self._handle_master_manual_select_date,
            "mbl": self._handle_master_manual_select_slot,
            "mbc": lambda user_id, _: self._handle_master_manual_confirm(telegram_user_id=user_id),
            "msc": lambda user_id, _: self._handle_master_cancel_start(telegram_user_id=user_id),
            "mci": self._handle_master_cancel_pick_booking,
            "mcr": self._handle_master_cancel_pick_reason,
            "mcn": lambda user_id, _: self._handle_master_cancel_confirm(telegram_user_id=user_id),
            "maa": lambda user_id, _: self._handle_master_admin_add_start(telegram_user_id=user_id),
            "mau": self._handle_master_admin_add_apply,
            "mad": lambda user_id, _: self._handle_master_admin_remove_start(telegram_user_id=user_id),
            "mar": self._handle_master_admin_remove_apply,
            "man": lambda user_id, _: self._handle_master_admin_rename_start(telegram_user_id=user_id),
            "max": self._handle_master_admin_rename_select,
        }
        handler = handlers.get(payload.action)
        if handler is None:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        return handler(telegram_user_id, payload.context)

    def handle_text(self, *, telegram_user_id: int, text_value: str | None) -> CallbackHandleResult | None:
        if text_value is None:
            return None
        current_menu = self._state.current_menu(telegram_user_id)
        if current_menu not in {
            _MENU_MASTER_ADMIN_ADD_SELECT,
            _MENU_MASTER_ADMIN_ADD_NICKNAME_INPUT,
            _MENU_MASTER_ADMIN_RENAME_INPUT,
            _MENU_MASTER_MANUAL_CLIENT_INPUT,
        }:
            return None

        if current_menu == _MENU_MASTER_MANUAL_CLIENT_INPUT:
            service_type = self._state.get_context_value(telegram_user_id, "master_manual_service")
            slot_token = self._state.get_context_value(telegram_user_id, "master_manual_slot")
            if service_type is None or slot_token is None:
                return self._stale_response(telegram_user_id=telegram_user_id)
            manual_client_name = text_value.strip()
            if not manual_client_name:
                return CallbackHandleResult(
                    text=f"{RU_BOOKING_MESSAGES['manual_booking_client_required']}\n{_MASTER_MANUAL_CLIENT_PROMPT}",
                    reply_markup=build_master_manual_client_input_markup(),
                )
            if len(manual_client_name) > 160:
                return CallbackHandleResult(
                    text=f"{RU_BOOKING_MESSAGES['manual_booking_client_too_long']}\n{_MASTER_MANUAL_CLIENT_PROMPT}",
                    reply_markup=build_master_manual_client_input_markup(),
                )
            self._state.set_context_value(telegram_user_id, "master_manual_client_name", manual_client_name)
            self._state.set_menu(telegram_user_id, _MENU_MASTER_MANUAL_CONFIRM)
            try:
                slot_start = _parse_slot_token(slot_token)
            except ValueError:
                return self._invalid_response(telegram_user_id=telegram_user_id)
            return CallbackHandleResult(
                text=_build_master_manual_confirmation_text(
                    service_type=service_type,
                    slot_start=slot_start,
                    client_name=manual_client_name,
                ),
                reply_markup=build_master_manual_confirm_markup(),
            )

        if not self._is_bootstrap_master(telegram_user_id=telegram_user_id):
            observe_master_admin_outcome("rbac", "denied")
            emit_event(
                "master_admin_action",
                actor_telegram_user_id=telegram_user_id,
                target_telegram_user_id=None,
                action="rbac",
                outcome="denied",
                reason="bootstrap_only",
            )
            return CallbackHandleResult(
                text=RU_MESSAGES["forbidden"],
                reply_markup=build_menu_markup(_MENU_MASTER),
            )

        if current_menu in {_MENU_MASTER_ADMIN_ADD_SELECT, _MENU_MASTER_ADMIN_ADD_NICKNAME_INPUT}:
            result = self._master_admin.add_master_by_nickname(raw_nickname=text_value)
            outcome = "success" if result.applied else "rejected"
            observe_master_admin_outcome("add", outcome)
            emit_event(
                "master_admin_action",
                actor_telegram_user_id=telegram_user_id,
                target_telegram_user_id=result.target_telegram_user_id,
                action="add",
                outcome=outcome,
                reason=result.reason,
            )

            if result.applied:
                self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN, reset_context=True)
                return CallbackHandleResult(
                    text=result.message,
                    reply_markup=build_menu_markup(_MENU_MASTER_ADMIN),
                )

            self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN_ADD_NICKNAME_INPUT)
            return CallbackHandleResult(
                text=f"{result.message}\n{_MASTER_ADMIN_ADD_NICKNAME_PROMPT}",
                reply_markup=build_master_admin_add_nickname_markup(),
            )

        target_telegram_user_id_raw = self._state.get_context_value(telegram_user_id, "rename_target_telegram_user_id")
        if target_telegram_user_id_raw is None:
            return self._stale_response(telegram_user_id=telegram_user_id)
        try:
            target_telegram_user_id = int(target_telegram_user_id_raw)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        result = self._master_admin.rename_master_display_name(
            telegram_user_id=target_telegram_user_id,
            raw_display_name=text_value,
        )
        outcome = "success" if result.applied else "rejected"
        observe_master_admin_outcome("rename", outcome)
        emit_event(
            "master_admin_action",
            actor_telegram_user_id=telegram_user_id,
            target_telegram_user_id=result.target_telegram_user_id,
            action="rename",
            outcome=outcome,
            reason=result.reason,
        )

        if result.applied:
            self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN, reset_context=True)
            return CallbackHandleResult(
                text=result.message,
                reply_markup=build_menu_markup(_MENU_MASTER_ADMIN),
            )

        self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN_RENAME_INPUT)
        return CallbackHandleResult(
            text=f"{result.message}\n{_MASTER_ADMIN_RENAME_PROMPT}",
            reply_markup=build_master_admin_add_nickname_markup(),
        )

    def _handle_static_menu_action(self, *, telegram_user_id: int, action: str) -> CallbackHandleResult:
        if action in {"hm", "bk"}:
            return self.start_menu(telegram_user_id=telegram_user_id)
        target_menu = _ACTION_TARGET_MENU[action]
        reset_context = target_menu in {_MENU_ROOT, _MENU_MASTER, _MENU_MASTER_ADMIN}
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

    def _handle_client_select_master(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None:
            return self._stale_response(telegram_user_id=telegram_user_id)
        try:
            master_id = int(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        response = self._flow.select_master(master_id)
        service_options = response.get("service_options", [])
        if not isinstance(service_options, list) or not service_options:
            self._state.set_menu(telegram_user_id, _MENU_CLIENT_MASTER_SELECT)
            return CallbackHandleResult(
                text=str(response.get("message", "Мастер не найден.")),
                reply_markup=build_menu_markup(_MENU_CLIENT),
            )

        self._state.set_context_value(telegram_user_id, "master_id", str(master_id))
        self._state.set_context_value(telegram_user_id, "master_name", self._resolve_master_display_name(master_id))
        self._state.set_menu(telegram_user_id, _MENU_CLIENT_SERVICE_SELECT)
        return CallbackHandleResult(
            text=str(response.get("message", "Выберите услугу.")),
            reply_markup=build_client_service_markup(service_options),
        )

    def _handle_client_select_service(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or context not in SERVICE_OPTION_LABELS_RU:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        if self._state.get_context_value(telegram_user_id, "master_id") is None:
            return self._stale_response(telegram_user_id=telegram_user_id)

        self._state.set_context_value(telegram_user_id, "service_type", context)
        self._state.set_context_value(telegram_user_id, "client_date_page", "0")
        self._state.set_menu(telegram_user_id, _MENU_CLIENT_DATE_SELECT)
        return CallbackHandleResult(
            text="Выберите дату для записи.",
            reply_markup=build_booking_date_markup(
                date_action="csd",
                page_action="cdp",
                page=0,
            ),
        )

    def _handle_client_date_page(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or not _PAGE_TOKEN_PATTERN.match(context):
            return self._invalid_response(telegram_user_id=telegram_user_id)
        if self._state.get_context_value(telegram_user_id, "master_id") is None:
            return self._stale_response(telegram_user_id=telegram_user_id)
        if self._state.get_context_value(telegram_user_id, "service_type") is None:
            return self._stale_response(telegram_user_id=telegram_user_id)
        try:
            page = _parse_page_token(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        max_page = _booking_max_page_index()
        if page < 0 or page > max_page:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        self._state.set_context_value(telegram_user_id, "client_date_page", str(page))
        self._state.set_menu(telegram_user_id, _MENU_CLIENT_DATE_SELECT)
        return CallbackHandleResult(
            text="Выберите дату для записи.",
            reply_markup=build_booking_date_markup(
                date_action="csd",
                page_action="cdp",
                page=page,
            ),
        )

    def _handle_client_select_date(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or not _DATE_TOKEN_PATTERN.match(context):
            return self._invalid_response(telegram_user_id=telegram_user_id)
        master_id_raw = self._state.get_context_value(telegram_user_id, "master_id")
        service_type = self._state.get_context_value(telegram_user_id, "service_type")
        if master_id_raw is None or service_type is None:
            return self._stale_response(telegram_user_id=telegram_user_id)
        try:
            master_id = int(master_id_raw)
            on_date = _parse_date_token(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        if not _is_date_in_booking_horizon(on_date):
            return self._invalid_response(telegram_user_id=telegram_user_id)

        self._state.set_context_value(telegram_user_id, "client_date_page", str(_booking_page_for_date(on_date)))

        response = self._flow.select_service(master_id=master_id, on_date=on_date, service_type=service_type)
        slots = response.get("slots", [])
        if not isinstance(slots, list) or not slots:
            self._state.set_menu(telegram_user_id, _MENU_CLIENT_DATE_SELECT)
            return CallbackHandleResult(
                text=f"{response.get('message', 'Выберите доступный слот.')}\nНа выбранную дату свободных слотов нет.",
                reply_markup=build_booking_date_markup(
                    date_action="csd",
                    page_action="cdp",
                    page=_booking_page_for_date(on_date),
                ),
            )

        self._state.set_menu(telegram_user_id, _MENU_CLIENT_SLOT_SELECT)
        return CallbackHandleResult(
            text=str(response.get("message", "Выберите доступный слот.")),
            reply_markup=build_slot_markup(slots, action="csl"),
        )

    def _handle_client_select_slot(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or not _SLOT_TOKEN_PATTERN.match(context):
            return self._invalid_response(telegram_user_id=telegram_user_id)
        master_id = self._state.get_context_value(telegram_user_id, "master_id")
        service_type = self._state.get_context_value(telegram_user_id, "service_type")
        if master_id is None or service_type is None:
            return self._stale_response(telegram_user_id=telegram_user_id)

        self._state.set_context_value(telegram_user_id, "slot_token", context)
        self._state.set_menu(telegram_user_id, _MENU_CLIENT_CONFIRM)
        slot_start = _parse_slot_token(context)
        master_name = self._state.get_context_value(telegram_user_id, "master_name") or _MASTER_DISPLAY_NAME_FALLBACK
        summary = (
            "Подтвердите запись:\n"
            f"- Мастер: {master_name}\n"
            f"- Услуга: {SERVICE_OPTION_LABELS_RU.get(service_type, service_type)}\n"
            f"- Слот: {format_ru_datetime(slot_start)}"
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
            return self._stale_response(telegram_user_id=telegram_user_id)

        try:
            master_id = int(master_id_raw)
            slot_start = _parse_slot_token(slot_token)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        response = self._flow.confirm(
            client_telegram_user_id=telegram_user_id,
            master_id=master_id,
            service_type=service_type,
            slot_start=slot_start,
        )
        result_message = str(response.get("message", ""))
        if response.get("created") is True:
            duration_minutes = self._resolve_service_duration_minutes(service_type=service_type)
            master_name = self._state.get_context_value(telegram_user_id, "master_name")
            if master_name is None:
                master_name = self._resolve_master_display_name(master_id)
            result_message = (
                f"{result_message}\n"
                f"Мастер: {master_name}\n"
                f"Слот: {format_ru_slot_range(slot_start, duration_minutes=duration_minutes)} "
                f"({format_ru_datetime(slot_start)})"
            ).strip()
        self._state.set_menu(telegram_user_id, _MENU_CLIENT, reset_context=True)
        return CallbackHandleResult(
            text=result_message,
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

    def _handle_client_cancel_prepare(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        try:
            booking_id = int(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        booking = self._find_client_booking_for_user(telegram_user_id=telegram_user_id, booking_id=booking_id)
        self._state.set_context_value(telegram_user_id, "cancel_booking_id", str(booking_id))
        if booking is not None:
            self._state.set_context_value(
                telegram_user_id,
                "cancel_slot_datetime",
                format_ru_datetime(booking["slot_start"]),
            )
        self._state.set_menu(telegram_user_id, _MENU_CLIENT_CANCEL_CONFIRM)
        summary = f"Подтвердите отмену записи #{booking_id}."
        if booking is not None:
            service_label = SERVICE_OPTION_LABELS_RU.get(booking["service_type"], booking["service_type"])
            summary = (
                f"{summary}\n"
                f"Слот: {format_ru_datetime(booking['slot_start'])}\n"
                f"Услуга: {service_label}"
            )
        return CallbackHandleResult(
            text=summary,
            reply_markup=build_client_cancel_confirm_markup(booking_id=booking_id),
        )

    def _handle_client_cancel_confirm(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        booking_id_raw = context or self._state.get_context_value(telegram_user_id, "cancel_booking_id")
        cancel_slot_dt = self._state.get_context_value(telegram_user_id, "cancel_slot_datetime")
        if booking_id_raw is None:
            return self._stale_response(telegram_user_id=telegram_user_id)
        try:
            booking_id = int(booking_id_raw)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        response = self._flow.cancel(
            client_telegram_user_id=telegram_user_id,
            booking_id=booking_id,
        )
        result_message = str(response.get("message", ""))
        if response.get("cancelled") is True and cancel_slot_dt is not None:
            result_message = f"{result_message}\nСлот: {cancel_slot_dt}"
        self._state.set_menu(telegram_user_id, _MENU_CLIENT, reset_context=True)
        return CallbackHandleResult(
            text=result_message,
            reply_markup=build_menu_markup(_MENU_CLIENT),
            notifications=_coerce_notifications(response.get("notifications")),
        )

    def _handle_master_view_schedule(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        master_ctx = self._schedule.resolve_context(master_telegram_user_id=telegram_user_id)
        if master_ctx is None:
            return CallbackHandleResult(
                text="Мастер не найден.",
                reply_markup=build_menu_markup(_MENU_MASTER),
            )

        if context is None:
            self._state.set_menu(telegram_user_id, _MENU_MASTER_SCHEDULE_DATE_SELECT)
            return CallbackHandleResult(
                text="Выберите дату для просмотра расписания.",
                reply_markup=build_client_date_markup(action="msv", action_back="mr", days_ahead=10),
            )

        if not _DATE_TOKEN_PATTERN.match(context):
            return self._invalid_response(telegram_user_id=telegram_user_id)

        try:
            on_date = _parse_date_token(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        day_start, day_end = business_day_bounds(on_date)
        with self._engine.connect() as conn:
            master = conn.execute(
                text(
                    """
                    SELECT display_name, lunch_start, lunch_end
                    FROM masters
                    WHERE id = :master_id
                    """
                ),
                {"master_id": master_ctx.master_id},
            ).mappings().first()
            rows = conn.execute(
                text(
                    """
                    SELECT
                        b.slot_start,
                        b.service_type,
                        b.manual_client_name,
                        COALESCE(b.client_username_snapshot, u.telegram_username) AS client_username,
                        COALESCE(b.client_phone_snapshot, u.phone_number) AS client_phone
                    FROM bookings b
                    LEFT JOIN users u ON u.id = b.client_user_id
                    WHERE b.master_id = :master_id
                      AND b.status = 'active'
                      AND b.slot_start >= :day_start
                      AND b.slot_start < :day_end
                    ORDER BY b.slot_start
                    """
                ),
                {"master_id": master_ctx.master_id, "day_start": day_start, "day_end": day_end},
            ).mappings()

        lines = [f"Расписание на {format_ru_date(on_date)}:"]
        if master is not None:
            lines.append(f"- Профиль: {master['display_name']}")
            lines.append(
                f"- Обед: {format_ru_time(dt_time.fromisoformat(str(master['lunch_start'])))} - "
                f"{format_ru_time(dt_time.fromisoformat(str(master['lunch_end'])))}"
            )
        has_rows = False
        for row in rows:
            slot_start = row["slot_start"]
            slot_start_dt = slot_start if isinstance(slot_start, datetime) else datetime.fromisoformat(str(slot_start))
            service_type = str(row["service_type"])
            client_line = _format_client_context(
                manual_client_name=_as_str_or_none(row["manual_client_name"]),
                client_username=_as_str_or_none(row["client_username"]),
                client_phone=_as_str_or_none(row["client_phone"]),
                fallback="не указан",
            )
            lines.append(
                f"- {format_ru_datetime(slot_start_dt)} ({SERVICE_OPTION_LABELS_RU.get(service_type, service_type)})\n"
                f"  {client_line}"
            )
            has_rows = True
        if not has_rows:
            lines.append("- Активных записей на выбранную дату нет.")

        self._state.set_menu(telegram_user_id, _MENU_MASTER)
        return CallbackHandleResult(
            text="\n".join(lines),
            reply_markup=build_menu_markup(_MENU_MASTER),
        )

    def _handle_master_day_off_start(self, *, telegram_user_id: int) -> CallbackHandleResult:
        self._state.set_menu(telegram_user_id, _MENU_MASTER_DAY_OFF_SELECT)
        return CallbackHandleResult(
            text="Выберите дату для выходного (рабочее окно мастера будет заблокировано на день).",
            reply_markup=build_master_day_off_markup(),
        )

    def _handle_master_day_off_apply(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or not _DATE_TOKEN_PATTERN.match(context):
            return self._invalid_response(telegram_user_id=telegram_user_id)
        try:
            on_date = _parse_date_token(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        master_ctx = self._schedule.resolve_context(master_telegram_user_id=telegram_user_id)
        if master_ctx is None:
            return CallbackHandleResult(
                text="Мастер не найден.",
                reply_markup=build_menu_markup(_MENU_MASTER),
            )
        work_window = self._resolve_master_work_window(master_ctx.master_id)
        if work_window is None:
            return CallbackHandleResult(
                text="Мастер не найден.",
                reply_markup=build_menu_markup(_MENU_MASTER),
            )
        work_start, work_end = work_window

        result = self._schedule.upsert_day_off(
            master_telegram_user_id=telegram_user_id,
            command=MasterDayOffCommand(
                start_at=combine_business_date_time(on_date, work_start),
                end_at=combine_business_date_time(on_date, work_end),
            ),
        )
        result_text = (
            f"{result.message}\n"
            f"Дата: {format_ru_date(on_date)}\n"
            f"Интервал: {format_ru_time(work_start)}-{format_ru_time(work_end)}"
        )
        self._state.set_menu(telegram_user_id, _MENU_MASTER, reset_context=True)
        return CallbackHandleResult(
            text=result_text,
            reply_markup=build_menu_markup(_MENU_MASTER),
        )

    def _handle_master_lunch_start(self, *, telegram_user_id: int) -> CallbackHandleResult:
        self._state.set_menu(telegram_user_id, _MENU_MASTER_LUNCH_SELECT)
        return CallbackHandleResult(
            text="Выберите новый обеденный интервал (60 минут).",
            reply_markup=build_master_lunch_markup(),
        )

    def _handle_master_lunch_apply(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or context not in _MASTER_LUNCH_PRESETS:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        lunch_start_raw, lunch_end_raw = _MASTER_LUNCH_PRESETS[context]
        lunch_start = dt_time.fromisoformat(lunch_start_raw)
        lunch_end = dt_time.fromisoformat(lunch_end_raw)
        result = self._schedule.update_lunch_break(
            master_telegram_user_id=telegram_user_id,
            command=MasterLunchBreakCommand(
                lunch_start=lunch_start,
                lunch_end=lunch_end,
            ),
        )
        result_text = (
            f"{result.message}\n"
            f"Новый интервал: {format_ru_time(lunch_start)}-{format_ru_time(lunch_end)}"
        )
        self._state.set_menu(telegram_user_id, _MENU_MASTER, reset_context=True)
        return CallbackHandleResult(
            text=result_text,
            reply_markup=build_menu_markup(_MENU_MASTER),
        )

    def _handle_master_manual_start(self, *, telegram_user_id: int) -> CallbackHandleResult:
        self._state.set_menu(telegram_user_id, _MENU_MASTER_MANUAL_SERVICE_SELECT, reset_context=True)
        return CallbackHandleResult(
            text="Выберите услугу для ручной записи.",
            reply_markup=build_master_service_markup(),
        )

    def _handle_master_manual_select_service(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or context not in SERVICE_OPTION_LABELS_RU:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        self._state.set_context_value(telegram_user_id, "master_manual_service", context)
        self._state.set_context_value(telegram_user_id, "master_manual_date_page", "0")
        self._state.set_menu(telegram_user_id, _MENU_MASTER_MANUAL_DATE_SELECT)
        return CallbackHandleResult(
            text="Выберите дату для ручной записи.",
            reply_markup=build_booking_date_markup(
                date_action="mbd",
                page_action="mbp",
                page=0,
                action_back="mr",
            ),
        )

    def _handle_master_manual_date_page(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or not _PAGE_TOKEN_PATTERN.match(context):
            return self._invalid_response(telegram_user_id=telegram_user_id)
        if self._state.get_context_value(telegram_user_id, "master_manual_service") is None:
            return self._stale_response(telegram_user_id=telegram_user_id)
        try:
            page = _parse_page_token(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        max_page = _booking_max_page_index()
        if page < 0 or page > max_page:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        self._state.set_context_value(telegram_user_id, "master_manual_date_page", str(page))
        self._state.set_menu(telegram_user_id, _MENU_MASTER_MANUAL_DATE_SELECT)
        return CallbackHandleResult(
            text="Выберите дату для ручной записи.",
            reply_markup=build_booking_date_markup(
                date_action="mbd",
                page_action="mbp",
                page=page,
                action_back="mr",
            ),
        )

    def _handle_master_manual_select_date(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or not _DATE_TOKEN_PATTERN.match(context):
            return self._invalid_response(telegram_user_id=telegram_user_id)
        service_type = self._state.get_context_value(telegram_user_id, "master_manual_service")
        if service_type is None:
            return self._stale_response(telegram_user_id=telegram_user_id)
        try:
            on_date = _parse_date_token(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        if not _is_date_in_booking_horizon(on_date):
            return self._invalid_response(telegram_user_id=telegram_user_id)
        self._state.set_context_value(telegram_user_id, "master_manual_date_page", str(_booking_page_for_date(on_date)))

        master_ctx = self._schedule.resolve_context(master_telegram_user_id=telegram_user_id)
        if master_ctx is None:
            return CallbackHandleResult(
                text="Мастер не найден.",
                reply_markup=build_menu_markup(_MENU_MASTER),
            )

        slots = self._flow.select_service(
            master_id=master_ctx.master_id,
            on_date=on_date,
            service_type=service_type,
        ).get("slots", [])
        if not isinstance(slots, list) or not slots:
            self._state.set_menu(telegram_user_id, _MENU_MASTER_MANUAL_DATE_SELECT)
            return CallbackHandleResult(
                text="На выбранную дату свободных слотов нет.",
                reply_markup=build_booking_date_markup(
                    date_action="mbd",
                    page_action="mbp",
                    page=_booking_page_for_date(on_date),
                    action_back="mr",
                ),
            )

        self._state.set_menu(telegram_user_id, _MENU_MASTER_MANUAL_SLOT_SELECT)
        return CallbackHandleResult(
            text="Выберите слот для ручной записи.",
            reply_markup=build_slot_markup(slots, action="mbl"),
        )

    def _handle_master_manual_select_slot(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or not _SLOT_TOKEN_PATTERN.match(context):
            return self._invalid_response(telegram_user_id=telegram_user_id)
        service_type = self._state.get_context_value(telegram_user_id, "master_manual_service")
        if service_type is None:
            return self._stale_response(telegram_user_id=telegram_user_id)

        self._state.set_context_value(telegram_user_id, "master_manual_slot", context)
        self._state.set_menu(telegram_user_id, _MENU_MASTER_MANUAL_CLIENT_INPUT)

        slot_start = _parse_slot_token(context)
        return CallbackHandleResult(
            text=(
                f"{_MASTER_MANUAL_CLIENT_PROMPT}\n"
                f"- Услуга: {SERVICE_OPTION_LABELS_RU.get(service_type, service_type)}\n"
                f"- Слот: {format_ru_datetime(slot_start)}"
            ),
            reply_markup=build_master_manual_client_input_markup(),
        )

    def _handle_master_manual_confirm(self, *, telegram_user_id: int) -> CallbackHandleResult:
        service_type = self._state.get_context_value(telegram_user_id, "master_manual_service")
        slot_token = self._state.get_context_value(telegram_user_id, "master_manual_slot")
        client_name = self._state.get_context_value(telegram_user_id, "master_manual_client_name")
        if service_type is None or slot_token is None or client_name is None:
            return self._stale_response(telegram_user_id=telegram_user_id)

        try:
            slot_start = _parse_slot_token(slot_token)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        result = self._schedule.create_manual_booking(
            master_telegram_user_id=telegram_user_id,
            command=MasterManualBookingCommand(
                client_name=client_name,
                service_type=service_type,
                slot_start=slot_start,
            ),
        )
        duration_minutes = self._resolve_service_duration_minutes(service_type=service_type)
        result_text = (
            f"{result.message}\n"
            f"Слот: {format_ru_slot_range(slot_start, duration_minutes=duration_minutes)} "
            f"({format_ru_datetime(slot_start)})\n"
            f"Услуга: {SERVICE_OPTION_LABELS_RU.get(service_type, service_type)}\n"
            f"Клиент: {client_name}"
        )
        self._state.set_menu(telegram_user_id, _MENU_MASTER, reset_context=True)
        return CallbackHandleResult(
            text=result_text,
            reply_markup=build_menu_markup(_MENU_MASTER),
        )

    def _handle_master_cancel_start(self, *, telegram_user_id: int) -> CallbackHandleResult:
        bookings = self._list_master_future_bookings(telegram_user_id=telegram_user_id)
        if not bookings:
            self._state.set_menu(telegram_user_id, _MENU_MASTER)
            return CallbackHandleResult(
                text="Нет активных записей для отмены.",
                reply_markup=build_menu_markup(_MENU_MASTER),
            )

        self._state.set_menu(telegram_user_id, _MENU_MASTER_CANCEL_SELECT)
        return CallbackHandleResult(
            text="Выберите запись клиента для отмены.",
            reply_markup=build_master_cancel_select_markup(bookings),
        )

    def _handle_master_cancel_pick_booking(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        try:
            booking_id = int(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        self._state.set_context_value(telegram_user_id, "master_cancel_booking_id", str(booking_id))
        booking = self._find_master_booking_for_user(telegram_user_id=telegram_user_id, booking_id=booking_id)
        if booking is not None:
            self._state.set_context_value(
                telegram_user_id,
                "master_cancel_slot_datetime",
                format_ru_datetime(booking["slot_start"]),
            )
            self._state.set_context_value(
                telegram_user_id,
                "master_cancel_service_type",
                booking["service_type"],
            )
        self._state.set_menu(telegram_user_id, _MENU_MASTER_CANCEL_REASON_SELECT)
        prompt = "Выберите причину отмены."
        if booking is not None:
            prompt = (
                f"{prompt}\n"
                f"Слот: {format_ru_datetime(booking['slot_start'])}\n"
                f"Услуга: {SERVICE_OPTION_LABELS_RU.get(booking['service_type'], booking['service_type'])}"
            )
        return CallbackHandleResult(
            text=prompt,
            reply_markup=build_master_cancel_reason_markup(),
        )

    def _handle_master_cancel_pick_reason(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None or context not in _MASTER_CANCEL_REASONS:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        booking_id = self._state.get_context_value(telegram_user_id, "master_cancel_booking_id")
        if booking_id is None:
            return self._stale_response(telegram_user_id=telegram_user_id)

        self._state.set_context_value(telegram_user_id, "master_cancel_reason_code", context)
        self._state.set_menu(telegram_user_id, _MENU_MASTER_CANCEL_CONFIRM)
        reason = _MASTER_CANCEL_REASONS[context]
        slot_dt = self._state.get_context_value(telegram_user_id, "master_cancel_slot_datetime")
        suffix = f"\nСлот: {slot_dt}" if slot_dt is not None else ""
        return CallbackHandleResult(
            text=f"Подтвердите отмену записи #{booking_id}. Причина: {reason}{suffix}",
            reply_markup=build_master_cancel_confirm_markup(),
        )

    def _handle_master_cancel_confirm(self, *, telegram_user_id: int) -> CallbackHandleResult:
        booking_id_raw = self._state.get_context_value(telegram_user_id, "master_cancel_booking_id")
        reason_code = self._state.get_context_value(telegram_user_id, "master_cancel_reason_code")
        slot_dt = self._state.get_context_value(telegram_user_id, "master_cancel_slot_datetime")
        if booking_id_raw is None or reason_code is None:
            return self._stale_response(telegram_user_id=telegram_user_id)
        if reason_code not in _MASTER_CANCEL_REASONS:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        try:
            booking_id = int(booking_id_raw)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        response = self._flow.cancel_by_master(
            master_telegram_user_id=telegram_user_id,
            booking_id=booking_id,
            reason=_MASTER_CANCEL_REASONS[reason_code],
        )
        result_text = str(response.get("message", ""))
        if response.get("cancelled") is True:
            reason_text = _MASTER_CANCEL_REASONS[reason_code]
            if slot_dt is not None:
                result_text = f"{result_text}\nСлот: {slot_dt}\nПричина: {reason_text}"
            else:
                result_text = f"{result_text}\nПричина: {reason_text}"
        self._state.set_menu(telegram_user_id, _MENU_MASTER, reset_context=True)
        return CallbackHandleResult(
            text=result_text,
            reply_markup=build_menu_markup(_MENU_MASTER),
            notifications=_coerce_notifications(response.get("notifications")),
        )

    def _handle_master_admin_add_start(self, *, telegram_user_id: int) -> CallbackHandleResult:
        self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN_ADD_NICKNAME_INPUT)
        return CallbackHandleResult(
            text=_MASTER_ADMIN_ADD_NICKNAME_PROMPT,
            reply_markup=build_master_admin_add_nickname_markup(),
        )

    def _handle_master_admin_add_apply(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        _ = context
        self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN_ADD_NICKNAME_INPUT)
        return CallbackHandleResult(
            text=_MASTER_ADMIN_ADD_NICKNAME_PROMPT,
            reply_markup=build_master_admin_add_nickname_markup(),
        )

    def _handle_master_admin_remove_start(self, *, telegram_user_id: int) -> CallbackHandleResult:
        removable = self._master_admin.list_removable_masters(
            bootstrap_master_telegram_user_id=self._bootstrap_master_telegram_user_id,
            limit=_MASTER_ADMIN_LIMIT,
        )
        if not removable:
            self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN)
            observe_master_admin_outcome("remove", "rejected")
            emit_event(
                "master_admin_action",
                actor_telegram_user_id=telegram_user_id,
                target_telegram_user_id=None,
                action="remove",
                outcome="rejected",
                reason="no_removable_masters",
            )
            return CallbackHandleResult(
                text="Нет активных мастеров для удаления.",
                reply_markup=build_menu_markup(_MENU_MASTER_ADMIN),
            )

        self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN_REMOVE_SELECT)
        return CallbackHandleResult(
            text="Выберите мастера для удаления из активных.",
            reply_markup=build_master_admin_remove_markup(removable),
        )

    def _handle_master_admin_remove_apply(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        try:
            target_telegram_user_id = int(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)

        result = self._master_admin.remove_master(
            telegram_user_id=target_telegram_user_id,
            bootstrap_master_telegram_user_id=self._bootstrap_master_telegram_user_id,
        )
        self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN, reset_context=True)
        observe_master_admin_outcome("remove", "success" if result.applied else "rejected")
        emit_event(
            "master_admin_action",
            actor_telegram_user_id=telegram_user_id,
            target_telegram_user_id=result.target_telegram_user_id,
            action="remove",
            outcome="success" if result.applied else "rejected",
            reason=result.reason,
        )
        return CallbackHandleResult(
            text=result.message,
            reply_markup=build_menu_markup(_MENU_MASTER_ADMIN),
        )

    def _handle_master_admin_rename_start(self, *, telegram_user_id: int) -> CallbackHandleResult:
        renamable = self._master_admin.list_renamable_masters(limit=_MASTER_ADMIN_LIMIT)
        if not renamable:
            self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN)
            observe_master_admin_outcome("rename", "rejected")
            emit_event(
                "master_admin_action",
                actor_telegram_user_id=telegram_user_id,
                target_telegram_user_id=None,
                action="rename",
                outcome="rejected",
                reason="no_renamable_masters",
            )
            return CallbackHandleResult(
                text="Нет активных мастеров для переименования.",
                reply_markup=build_menu_markup(_MENU_MASTER_ADMIN),
            )

        self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN_RENAME_SELECT)
        return CallbackHandleResult(
            text="Выберите мастера для переименования.",
            reply_markup=build_master_admin_rename_markup(renamable),
        )

    def _handle_master_admin_rename_select(self, telegram_user_id: int, context: str | None) -> CallbackHandleResult:
        if context is None:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        try:
            target_telegram_user_id = int(context)
        except ValueError:
            return self._invalid_response(telegram_user_id=telegram_user_id)
        self._state.set_context_value(telegram_user_id, "rename_target_telegram_user_id", str(target_telegram_user_id))
        self._state.set_menu(telegram_user_id, _MENU_MASTER_ADMIN_RENAME_INPUT)
        return CallbackHandleResult(
            text=f"Укажите новое имя для мастера tg:{target_telegram_user_id}.\n{_MASTER_ADMIN_RENAME_PROMPT}",
            reply_markup=build_master_admin_add_nickname_markup(),
        )

    def _is_bootstrap_master(self, *, telegram_user_id: int) -> bool:
        return telegram_user_id == self._bootstrap_master_telegram_user_id

    def _list_client_future_bookings(self, *, telegram_user_id: int) -> list[dict[str, object]]:
        client_user_id = self._flow_repo.resolve_client_user_id(telegram_user_id)
        if client_user_id is None:
            return []

        now_utc = utc_now()
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT b.id, b.slot_start, b.service_type, m.display_name
                    , m.id AS master_id
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
                slot_start = _as_datetime(row["slot_start"])
                result.append(
                    {
                        "id": int(row["id"]),
                        "slot_start": slot_start,
                        "service_type": str(row["service_type"]),
                        "master_name": _format_master_display_name(
                            master_id=int(row["master_id"]),
                            raw_display_name=row["display_name"],
                        ),
                    }
                )
            return result

    def _find_client_booking_for_user(self, *, telegram_user_id: int, booking_id: int) -> dict[str, object] | None:
        for booking in self._list_client_future_bookings(telegram_user_id=telegram_user_id):
            if booking["id"] == booking_id:
                return booking
        return None

    def _find_master_booking_for_user(self, *, telegram_user_id: int, booking_id: int) -> dict[str, object] | None:
        for booking in self._list_master_future_bookings(telegram_user_id=telegram_user_id):
            if booking["id"] == booking_id:
                return booking
        return None

    def _resolve_service_duration_minutes(self, *, service_type: str) -> int:
        with self._engine.connect() as conn:
            duration = resolve_service_duration_minutes(service_type, connection=conn)
        return duration if duration is not None else 60

    def _list_master_future_bookings(self, *, telegram_user_id: int) -> list[dict[str, object]]:
        master_ctx = self._schedule.resolve_context(master_telegram_user_id=telegram_user_id)
        if master_ctx is None:
            return []

        now_utc = utc_now()
        with self._engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT b.id, b.slot_start, b.service_type
                    FROM bookings b
                    WHERE b.master_id = :master_id
                      AND b.status = 'active'
                      AND b.slot_start >= :now_utc
                    ORDER BY b.slot_start
                    LIMIT 20
                    """
                ),
                {"master_id": master_ctx.master_id, "now_utc": now_utc},
            ).mappings()
            result: list[dict[str, object]] = []
            for row in rows:
                result.append(
                    {
                        "id": int(row["id"]),
                        "slot_start": _as_datetime(row["slot_start"]),
                        "service_type": str(row["service_type"]),
                    }
                )
            return result

    def _resolve_master_work_window(self, master_id: int) -> tuple[dt_time, dt_time] | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT work_start, work_end
                    FROM masters
                    WHERE id = :master_id
                    """
                ),
                {"master_id": master_id},
            ).mappings().first()
            if row is None:
                return None
            return dt_time.fromisoformat(str(row["work_start"])), dt_time.fromisoformat(str(row["work_end"]))

    def _invalid_response(self, *, telegram_user_id: int) -> CallbackHandleResult:
        return CallbackHandleResult(
            text=RU_MESSAGES["invalid_callback"],
            reply_markup=self._default_markup_for_user(telegram_user_id),
        )

    def _stale_response(self, *, telegram_user_id: int) -> CallbackHandleResult:
        return CallbackHandleResult(
            text=RU_MESSAGES["stale_callback"],
            reply_markup=self._default_markup_for_user(telegram_user_id),
        )

    def _default_markup_for_user(self, telegram_user_id: int) -> InlineKeyboardMarkup:
        role = self._roles.resolve_role(telegram_user_id)
        if role is None:
            return build_root_menu_markup()
        return self._default_markup_for_role(role)

    @staticmethod
    def _default_markup_for_role(role: str) -> InlineKeyboardMarkup:
        if role == "Client":
            return build_menu_markup(_MENU_CLIENT)
        if role == "Master":
            return build_menu_markup(_MENU_MASTER)
        return build_root_menu_markup()

    def _resolve_master_display_name(self, master_id: int) -> str:
        with self._engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT display_name
                    FROM masters
                    WHERE id = :master_id
                    """
                ),
                {"master_id": master_id},
            ).mappings().first()
        raw_name = row["display_name"] if row is not None else None
        return _format_master_display_name(master_id=master_id, raw_display_name=raw_name)


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
    return normalize_utc(parsed)


def _format_slot_token(slot_start: datetime) -> str:
    return slot_start.astimezone(UTC).strftime("%Y%m%d%H%M")


def _parse_date_token(token: str) -> date:
    if not _DATE_TOKEN_PATTERN.match(token):
        raise ValueError("Invalid date token")
    return datetime.strptime(token, "%Y%m%d").date()


def _parse_page_token(token: str) -> int:
    if not _PAGE_TOKEN_PATTERN.match(token):
        raise ValueError("Invalid page token")
    return int(token[1:])


def _format_page_token(page: int) -> str:
    if page < 0:
        raise ValueError("Page index must be non-negative")
    return f"p{page}"


def _booking_date_horizon(*, today: date | None = None) -> tuple[date, date]:
    start = today or business_now().date()
    end = start + timedelta(days=BOOKING_DATE_HORIZON_DAYS - 1)
    return start, end


def _booking_page_for_date(on_date: date, *, today: date | None = None) -> int:
    start, end = _booking_date_horizon(today=today)
    if on_date < start:
        return 0
    if on_date > end:
        return _booking_max_page_index()
    return (on_date - start).days // BOOKING_DATE_PAGE_SIZE


def _booking_max_page_index() -> int:
    return (BOOKING_DATE_HORIZON_DAYS - 1) // BOOKING_DATE_PAGE_SIZE


def _is_date_in_booking_horizon(on_date: date, *, today: date | None = None) -> bool:
    start, end = _booking_date_horizon(today=today)
    return start <= on_date <= end


def _as_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return normalize_utc(value)
    parsed = datetime.fromisoformat(str(value))
    return normalize_utc(parsed)


def _as_str_or_none(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _format_client_context(
    *,
    manual_client_name: str | None,
    client_username: str | None,
    client_phone: str | None,
    fallback: str,
) -> str:
    if manual_client_name and manual_client_name.strip():
        client = manual_client_name.strip()
    elif client_username and client_username.strip():
        client = f"@{client_username.strip().lstrip('@')}"
    else:
        client = fallback
    if client_phone and client_phone.strip():
        return f"Клиент: {client}; телефон: {client_phone.strip()}"
    return f"Клиент: {client}"


def _build_master_manual_confirmation_text(
    *,
    service_type: str,
    slot_start: datetime,
    client_name: str,
) -> str:
    return (
        "Подтвердите ручную запись:\n"
        f"- Услуга: {SERVICE_OPTION_LABELS_RU.get(service_type, service_type)}\n"
        f"- Слот: {format_ru_datetime(slot_start)}\n"
        f"- Клиент: {client_name}"
    )


def build_root_menu_markup() -> InlineKeyboardMarkup:
    return build_menu_markup(_MENU_ROOT)


def build_menu_markup(menu: str) -> InlineKeyboardMarkup:
    if menu == _MENU_CLIENT:
        rows = chunk_inline_buttons(
            [
                InlineKeyboardButton(text="Новая запись", callback_data=encode_callback_data(action="cb")),
                InlineKeyboardButton(text="Отменить запись", callback_data=encode_callback_data(action="cc")),
            ],
            max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW,
        )
    elif menu == _MENU_MASTER:
        rows = chunk_inline_buttons(
            [
                InlineKeyboardButton(text="Просмотр расписания", callback_data=encode_callback_data(action="msv")),
                InlineKeyboardButton(text="Выходной день", callback_data=encode_callback_data(action="msd")),
                InlineKeyboardButton(text="Обед", callback_data=encode_callback_data(action="mlm")),
                InlineKeyboardButton(text="Ручная запись", callback_data=encode_callback_data(action="msb")),
                InlineKeyboardButton(text="Отмена записи", callback_data=encode_callback_data(action="msc")),
                InlineKeyboardButton(text="Управление мастерами", callback_data=encode_callback_data(action="mam")),
            ],
            max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW,
        )
    elif menu == _MENU_MASTER_ADMIN:
        rows = chunk_inline_buttons(
            [
                InlineKeyboardButton(text="Добавить мастера", callback_data=encode_callback_data(action="maa")),
                InlineKeyboardButton(text="Удалить мастера", callback_data=encode_callback_data(action="mad")),
                InlineKeyboardButton(text="Переименовать мастера", callback_data=encode_callback_data(action="man")),
            ],
            max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW,
        )
        rows.extend(_back_and_home_rows(action_back="mr"))
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
    buttons: list[InlineKeyboardButton] = []
    for item in masters:
        if not isinstance(item, dict):
            continue
        master_id = item.get("id")
        if not isinstance(master_id, int):
            continue
        name = _format_master_display_name(master_id=master_id, raw_display_name=item.get("display_name"))
        buttons.append(
            InlineKeyboardButton(
                text=name,
                callback_data=encode_callback_data(action="csm", context=str(master_id)),
            )
        )
    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW)
    rows.extend(_back_and_home_rows(action_back="bk"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_client_service_markup(service_options: list[object]) -> InlineKeyboardMarkup:
    buttons = _service_buttons(service_options=service_options, action="css")
    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW)
    rows.extend(_back_and_home_rows(action_back="bk"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_master_service_markup() -> InlineKeyboardMarkup:
    buttons = _service_buttons(service_options=list_service_options(), action="mbs")
    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW)
    rows.extend(_back_and_home_rows(action_back="mr"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_booking_date_markup(
    *,
    date_action: str,
    page_action: str,
    page: int = 0,
    action_back: str = "bk",
) -> InlineKeyboardMarkup:
    today = business_now().date()
    start_date, _ = _booking_date_horizon(today=today)
    max_page = _booking_max_page_index()
    current_page = min(max(page, 0), max_page)
    start_index = current_page * BOOKING_DATE_PAGE_SIZE
    end_index = min(start_index + BOOKING_DATE_PAGE_SIZE, BOOKING_DATE_HORIZON_DAYS)

    buttons: list[InlineKeyboardButton] = []
    for offset in range(start_index, end_index):
        day = start_date + timedelta(days=offset)
        token = day.strftime("%Y%m%d")
        buttons.append(
            InlineKeyboardButton(
                text=format_ru_date(day),
                callback_data=encode_callback_data(action=date_action, context=token),
            )
        )

    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_DATE_SLOT_MAX_BUTTONS_PER_ROW)
    navigation_buttons: list[InlineKeyboardButton] = []
    if current_page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Назад по датам",
                callback_data=encode_callback_data(action=page_action, context=_format_page_token(current_page - 1)),
            )
        )
    if current_page < max_page:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперед по датам",
                callback_data=encode_callback_data(action=page_action, context=_format_page_token(current_page + 1)),
            )
        )
    if navigation_buttons:
        rows.extend(chunk_inline_buttons(navigation_buttons, max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW))
    rows.extend(_back_and_home_rows(action_back=action_back))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_client_date_markup(*, action: str, days_ahead: int = 7, action_back: str = "bk") -> InlineKeyboardMarkup:
    today = business_now().date()
    buttons: list[InlineKeyboardButton] = []
    for offset in range(days_ahead):
        day = today + timedelta(days=offset)
        token = day.strftime("%Y%m%d")
        buttons.append(
            InlineKeyboardButton(
                text=format_ru_date(day),
                callback_data=encode_callback_data(action=action, context=token),
            )
        )
    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_DATE_SLOT_MAX_BUTTONS_PER_ROW)
    rows.extend(_back_and_home_rows(action_back=action_back))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_slot_markup(slots: list[object], *, action: str, action_back: str = "bk") -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    for item in slots:
        if not isinstance(item, dict):
            continue
        start_at = item.get("start_at")
        end_at = item.get("end_at")
        if not isinstance(start_at, str):
            continue
        slot_start = _as_datetime(start_at)
        slot_end = _as_datetime(end_at) if isinstance(end_at, str) else slot_start
        duration_minutes = max(1, int((slot_end - slot_start).total_seconds() // 60))
        token = _format_slot_token(slot_start)
        buttons.append(
            InlineKeyboardButton(
                text=format_ru_slot_range(slot_start, duration_minutes=duration_minutes),
                callback_data=encode_callback_data(action=action, context=token),
            )
        )
    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_DATE_SLOT_MAX_BUTTONS_PER_ROW)
    rows.extend(_back_and_home_rows(action_back=action_back))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_client_confirm_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить", callback_data=encode_callback_data(action="ccf"))],
            *(_back_and_home_rows(action_back="bk")),
        ]
    )


def build_master_manual_confirm_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать ручную запись", callback_data=encode_callback_data(action="mbc"))],
            *(_back_and_home_rows(action_back="mr")),
        ]
    )


def build_master_manual_client_input_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=_back_and_home_rows(action_back="mr"))


def build_client_cancel_select_markup(bookings: list[dict[str, object]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for booking in bookings:
        booking_id = booking.get("id")
        slot_start = booking.get("slot_start")
        master_name = booking.get("master_name")
        if not isinstance(booking_id, int) or not isinstance(slot_start, datetime) or not isinstance(master_name, str):
            continue
        label = f"#{booking_id} {format_ru_datetime(slot_start)} {master_name}"
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=encode_callback_data(action="cci", context=str(booking_id)),
                )
            ]
        )
    rows.extend(_back_and_home_rows(action_back="bk"))
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
            *(_back_and_home_rows(action_back="bk")),
        ]
    )


def build_master_day_off_markup() -> InlineKeyboardMarkup:
    return build_client_date_markup(action="msu", action_back="mr", days_ahead=10)


def build_master_lunch_markup() -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    for preset_code, (start_at, end_at) in _MASTER_LUNCH_PRESETS.items():
        buttons.append(
            InlineKeyboardButton(
                text=f"{start_at[:5]}-{end_at[:5]}",
                callback_data=encode_callback_data(action="mls", context=preset_code),
            )
        )
    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW)
    rows.extend(_back_and_home_rows(action_back="mr"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_master_cancel_select_markup(bookings: list[dict[str, object]]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for booking in bookings:
        booking_id = booking.get("id")
        slot_start = booking.get("slot_start")
        service_type = booking.get("service_type")
        if not isinstance(booking_id, int) or not isinstance(slot_start, datetime) or not isinstance(service_type, str):
            continue
        label = (
            f"#{booking_id} {format_ru_datetime(slot_start)} "
            f"{SERVICE_OPTION_LABELS_RU.get(service_type, service_type)}"
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=encode_callback_data(action="mci", context=str(booking_id)),
                )
            ]
        )
    rows.extend(_back_and_home_rows(action_back="mr"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_master_cancel_reason_markup() -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    for reason_code, reason_text in _MASTER_CANCEL_REASONS.items():
        buttons.append(
            InlineKeyboardButton(
                text=reason_text,
                callback_data=encode_callback_data(action="mcr", context=reason_code),
            )
        )
    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW)
    rows.extend(_back_and_home_rows(action_back="mr"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_master_cancel_confirm_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить отмену", callback_data=encode_callback_data(action="mcn"))],
            *(_back_and_home_rows(action_back="mr")),
        ]
    )


def build_master_admin_add_nickname_markup() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    rows.extend(_back_and_home_rows(action_back="mr"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_master_admin_remove_markup(masters: list[dict[str, object]]) -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    for item in masters:
        telegram_user_id = item.get("telegram_user_id")
        display_name = item.get("display_name")
        if not isinstance(telegram_user_id, int) or not isinstance(display_name, str):
            continue
        buttons.append(
            InlineKeyboardButton(
                text=f"{display_name} (tg:{telegram_user_id})",
                callback_data=encode_callback_data(action="mar", context=str(telegram_user_id)),
            )
        )
    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW)
    rows.extend(_back_and_home_rows(action_back="mr"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_master_admin_rename_markup(masters: list[dict[str, object]]) -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    for item in masters:
        telegram_user_id = item.get("telegram_user_id")
        display_name = item.get("display_name")
        if not isinstance(telegram_user_id, int) or not isinstance(display_name, str):
            continue
        buttons.append(
            InlineKeyboardButton(
                text=f"{display_name} (tg:{telegram_user_id})",
                callback_data=encode_callback_data(action="max", context=str(telegram_user_id)),
            )
        )
    rows = chunk_inline_buttons(buttons, max_per_row=MOBILE_MENU_MAX_BUTTONS_PER_ROW)
    rows.extend(_back_and_home_rows(action_back="mr"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _service_rows(*, service_options: list[object], action: str) -> list[list[InlineKeyboardButton]]:
    return [[button] for button in _service_buttons(service_options=service_options, action=action)]


def _service_buttons(*, service_options: list[object], action: str) -> list[InlineKeyboardButton]:
    buttons: list[InlineKeyboardButton] = []
    for item in service_options:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        label = item.get("label")
        if not isinstance(code, str) or not isinstance(label, str):
            continue
        buttons.append(
            InlineKeyboardButton(
                text=label,
                callback_data=encode_callback_data(action=action, context=code),
            )
        )
    return buttons


def _back_and_home_rows(*, action_back: str) -> list[list[InlineKeyboardButton]]:
    return [
        [InlineKeyboardButton(text="Назад", callback_data=encode_callback_data(action=action_back))],
    ]


def _format_master_display_name(*, master_id: int, raw_display_name: object) -> str:
    if isinstance(raw_display_name, str):
        normalized = raw_display_name.strip()
        if normalized:
            return normalized
    _ = master_id
    return _MASTER_DISPLAY_NAME_FALLBACK


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
