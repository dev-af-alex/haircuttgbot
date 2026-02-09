from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from sqlalchemy.engine import Engine

from app.auth import RoleRepository, authorize_command
from app.auth.messages import RU_MESSAGES
from app.booking import (
    MasterDayOffCommand,
    MasterLunchBreakCommand,
    MasterManualBookingCommand,
    MasterScheduleService,
    TelegramBookingFlowService,
)

_HELP_TEXT = """Доступные команды:
/start
/help
/client_start
/client_master <master_id>
/client_slots <master_id> <service_type> <YYYY-MM-DD>
/client_book <master_id> <service_type> <YYYY-MM-DDTHH:MM:SS+00:00>
/client_cancel <booking_id>
/master_cancel <booking_id> <reason>
/master_dayoff <YYYY-MM-DDTHH:MM:SS+00:00> <YYYY-MM-DDTHH:MM:SS+00:00> [block_id]
/master_lunch <HH:MM:SS> <HH:MM:SS>
/master_manual <service_type> <YYYY-MM-DDTHH:MM:SS+00:00> <client_name>
"""


@dataclass(frozen=True)
class TelegramCommandResult:
    text: str
    notifications: list[dict[str, object]]


class TelegramCommandService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._roles = RoleRepository(engine)
        self._flow = TelegramBookingFlowService(engine)
        self._schedule = MasterScheduleService(engine)

    def help(self, *, telegram_user_id: int) -> TelegramCommandResult:
        role = self._roles.resolve_role(telegram_user_id)
        if role is None:
            return TelegramCommandResult(text=RU_MESSAGES["unknown_user"], notifications=[])
        return TelegramCommandResult(
            text=f"Роль: {role}\n{_HELP_TEXT}".strip(),
            notifications=[],
        )

    def client_start(self, *, telegram_user_id: int) -> TelegramCommandResult:
        denied = self._deny_if_forbidden(telegram_user_id=telegram_user_id, command="client:book")
        if denied is not None:
            return denied

        response = self._flow.start()
        masters = response.get("masters", [])
        lines = [str(response.get("message", ""))]
        for master in masters:
            lines.append(f"- {master['display_name']}")
        return TelegramCommandResult(text="\n".join(lines).strip(), notifications=[])

    def client_select_master(self, *, telegram_user_id: int, master_id: int) -> TelegramCommandResult:
        denied = self._deny_if_forbidden(telegram_user_id=telegram_user_id, command="client:book")
        if denied is not None:
            return denied

        response = self._flow.select_master(master_id)
        options = response.get("service_options", [])
        lines = [str(response.get("message", ""))]
        for option in options:
            lines.append(f"- {option['code']}: {option['label']}")
        return TelegramCommandResult(text="\n".join(lines).strip(), notifications=[])

    def client_slots(
        self,
        *,
        telegram_user_id: int,
        master_id: int,
        service_type: str,
        on_date: date,
    ) -> TelegramCommandResult:
        denied = self._deny_if_forbidden(telegram_user_id=telegram_user_id, command="client:book")
        if denied is not None:
            return denied

        response = self._flow.select_service(master_id=master_id, on_date=on_date, service_type=service_type)
        slots = response.get("slots", [])
        lines = [str(response.get("message", ""))]
        for slot in slots:
            lines.append(f"- {slot['start_at']} -> {slot['end_at']}")
        return TelegramCommandResult(text="\n".join(lines).strip(), notifications=[])

    def client_confirm(
        self,
        *,
        telegram_user_id: int,
        master_id: int,
        service_type: str,
        slot_start: datetime,
    ) -> TelegramCommandResult:
        denied = self._deny_if_forbidden(telegram_user_id=telegram_user_id, command="client:book")
        if denied is not None:
            return denied

        response = self._flow.confirm(
            client_telegram_user_id=telegram_user_id,
            master_id=master_id,
            service_type=service_type,
            slot_start=slot_start,
        )
        return TelegramCommandResult(
            text=str(response.get("message", "")),
            notifications=_coerce_notifications(response.get("notifications")),
        )

    def client_cancel(self, *, telegram_user_id: int, booking_id: int) -> TelegramCommandResult:
        denied = self._deny_if_forbidden(telegram_user_id=telegram_user_id, command="client:cancel")
        if denied is not None:
            return denied

        response = self._flow.cancel(
            client_telegram_user_id=telegram_user_id,
            booking_id=booking_id,
        )
        return TelegramCommandResult(
            text=str(response.get("message", "")),
            notifications=_coerce_notifications(response.get("notifications")),
        )

    def master_cancel(
        self,
        *,
        telegram_user_id: int,
        booking_id: int,
        reason: str,
    ) -> TelegramCommandResult:
        denied = self._deny_if_forbidden(telegram_user_id=telegram_user_id, command="master:schedule")
        if denied is not None:
            return denied

        response = self._flow.cancel_by_master(
            master_telegram_user_id=telegram_user_id,
            booking_id=booking_id,
            reason=reason,
        )
        return TelegramCommandResult(
            text=str(response.get("message", "")),
            notifications=_coerce_notifications(response.get("notifications")),
        )

    def master_day_off(
        self,
        *,
        telegram_user_id: int,
        start_at: datetime,
        end_at: datetime,
        block_id: int | None = None,
    ) -> TelegramCommandResult:
        denied = self._deny_if_forbidden(telegram_user_id=telegram_user_id, command="master:day-off")
        if denied is not None:
            return denied

        result = self._schedule.upsert_day_off(
            master_telegram_user_id=telegram_user_id,
            command=MasterDayOffCommand(start_at=start_at, end_at=end_at, block_id=block_id),
        )
        return TelegramCommandResult(text=result.message, notifications=[])

    def master_lunch(
        self,
        *,
        telegram_user_id: int,
        lunch_start: time,
        lunch_end: time,
    ) -> TelegramCommandResult:
        denied = self._deny_if_forbidden(telegram_user_id=telegram_user_id, command="master:lunch")
        if denied is not None:
            return denied

        result = self._schedule.update_lunch_break(
            master_telegram_user_id=telegram_user_id,
            command=MasterLunchBreakCommand(lunch_start=lunch_start, lunch_end=lunch_end),
        )
        return TelegramCommandResult(text=result.message, notifications=[])

    def master_manual(
        self,
        *,
        telegram_user_id: int,
        client_name: str,
        service_type: str,
        slot_start: datetime,
    ) -> TelegramCommandResult:
        denied = self._deny_if_forbidden(telegram_user_id=telegram_user_id, command="master:schedule")
        if denied is not None:
            return denied

        result = self._schedule.create_manual_booking(
            master_telegram_user_id=telegram_user_id,
            command=MasterManualBookingCommand(
                client_name=client_name,
                service_type=service_type,
                slot_start=slot_start,
            ),
        )
        return TelegramCommandResult(text=result.message, notifications=[])

    def _deny_if_forbidden(self, *, telegram_user_id: int, command: str) -> TelegramCommandResult | None:
        role = self._roles.resolve_role(telegram_user_id)
        decision = authorize_command(command, role)
        if decision.allowed:
            return None
        return TelegramCommandResult(text=decision.message, notifications=[])


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
