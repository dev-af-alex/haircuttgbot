import logging
import os
from json import loads
from contextlib import asynccontextmanager
from datetime import date, datetime, time
from json import JSONDecodeError
from typing import Any

from aiogram import Dispatcher
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.auth import RoleRepository, authorize_command
from app.booking import (
    AvailabilityService,
    BookingService,
    MasterDayOffCommand,
    MasterLunchBreakCommand,
    MasterManualBookingCommand,
    MasterScheduleService,
    TelegramBookingFlowService,
    list_service_options,
)
from app.db.session import get_engine
from app.idempotency import CachedHttpResponse, TelegramIdempotencyStore
from app.observability import (
    emit_event,
    instrument_endpoint,
    observe_abuse_outcome,
    render_metrics,
    set_service_health,
)
from app.throttling import TelegramCommandThrottle

logging.basicConfig(level=logging.INFO, format="%(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Keep aiogram integration point present in runtime skeleton.
    _dispatcher = Dispatcher()
    _ = _dispatcher

    set_service_health(True)
    emit_event("startup", telegram_token_configured=bool(bot_token))
    yield


app = FastAPI(title="haircuttgbot-api", version="0.1.0", lifespan=lifespan)
app.state.telegram_throttle = TelegramCommandThrottle(
    limit=int(os.getenv("TELEGRAM_THROTTLE_LIMIT", "8")),
    window_seconds=int(os.getenv("TELEGRAM_THROTTLE_WINDOW_SECONDS", "10")),
)
app.state.telegram_idempotency = TelegramIdempotencyStore(
    window_seconds=int(os.getenv("TELEGRAM_IDEMPOTENCY_WINDOW_SECONDS", "120")),
)

_THROTTLED_PATH_PREFIX = "/internal/telegram/"
_THROTTLED_METHODS = {"POST"}
_THROTTLED_USER_KEYS = (
    "client_telegram_user_id",
    "master_telegram_user_id",
    "telegram_user_id",
)
_IDEMPOTENT_OUTCOME_BY_PATH = {
    "/internal/telegram/client/booking-flow/confirm": "created",
    "/internal/telegram/client/booking-flow/cancel": "cancelled",
    "/internal/telegram/master/booking-flow/cancel": "cancelled",
    "/internal/telegram/master/schedule/day-off": "applied",
    "/internal/telegram/master/schedule/lunch": "applied",
    "/internal/telegram/master/schedule/manual-booking": "applied",
}


def _extract_telegram_user_id(payload: Any) -> int | None:
    if not isinstance(payload, dict):
        return None
    for key in _THROTTLED_USER_KEYS:
        value = payload.get(key)
        if isinstance(value, int):
            return value
    return None


@app.middleware("http")
async def telegram_command_guards(request: Request, call_next):  # type: ignore[no-untyped-def]
    if request.method not in _THROTTLED_METHODS or not request.url.path.startswith(_THROTTLED_PATH_PREFIX):
        return await call_next(request)

    telegram_user_id: int | None = None
    payload_dict: dict[str, Any] | None = None
    try:
        payload = await request.json()
        payload_dict = payload if isinstance(payload, dict) else None
        telegram_user_id = _extract_telegram_user_id(payload)
    except (JSONDecodeError, UnicodeDecodeError):
        payload = None
        _ = payload

    if telegram_user_id is None:
        return await call_next(request)

    idempotent_outcome_key = _IDEMPOTENT_OUTCOME_BY_PATH.get(request.url.path)
    idempotency_key: str | None = None
    if idempotent_outcome_key is not None and payload_dict is not None:
        idempotency_key = app.state.telegram_idempotency.make_key(
            path=request.url.path,
            telegram_user_id=telegram_user_id,
            payload=payload_dict,
        )
        cached = app.state.telegram_idempotency.get(idempotency_key)
        if cached is not None:
            emit_event(
                "telegram_idempotency_replay",
                telegram_user_id=telegram_user_id,
                path=request.url.path,
                idempotency_window_seconds=app.state.telegram_idempotency.window_seconds,
            )
            return Response(
                content=cached.body,
                status_code=cached.status_code,
                media_type=cached.media_type,
                headers={"X-Idempotency-Replayed": "1"},
            )

    decision = app.state.telegram_throttle.check(telegram_user_id)
    observe_abuse_outcome(request.url.path, allowed=decision.allowed)

    if not decision.allowed:
        emit_event(
            "abuse_throttle_deny",
            telegram_user_id=telegram_user_id,
            path=request.url.path,
            method=request.method,
            window_seconds=app.state.telegram_throttle.window_seconds,
            limit=app.state.telegram_throttle.limit,
            retry_after_seconds=decision.retry_after_seconds,
        )
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Слишком много запросов. Повторите позже.",
                "code": "throttled",
                "retry_after_seconds": decision.retry_after_seconds,
            },
        )

    response = await call_next(request)

    if idempotency_key is None or idempotent_outcome_key is None:
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    media_type = response.media_type or "application/json"
    replay_safe = Response(
        content=body,
        status_code=response.status_code,
        media_type=media_type,
        headers=dict(response.headers),
    )

    if response.status_code == 200:
        try:
            payload = loads(body.decode("utf-8"))
        except Exception:
            payload = None
        if isinstance(payload, dict) and payload.get(idempotent_outcome_key) is True:
            app.state.telegram_idempotency.put(
                idempotency_key,
                CachedHttpResponse(
                    status_code=response.status_code,
                    body=body,
                    media_type=media_type,
                ),
            )

    return replay_safe


class ResolveRoleRequest(BaseModel):
    telegram_user_id: int


class AuthorizeCommandRequest(BaseModel):
    telegram_user_id: int
    command: str


class AvailabilityRequest(BaseModel):
    master_id: int
    date: date


class CreateBookingRequest(BaseModel):
    master_id: int
    client_user_id: int
    service_type: str
    slot_start: datetime


class TelegramFlowMasterRequest(BaseModel):
    master_id: int


class TelegramFlowServiceRequest(BaseModel):
    master_id: int
    date: date


class TelegramFlowConfirmRequest(BaseModel):
    client_telegram_user_id: int
    master_id: int
    service_type: str
    slot_start: datetime


class TelegramFlowCancelRequest(BaseModel):
    client_telegram_user_id: int
    booking_id: int


class TelegramFlowMasterCancelRequest(BaseModel):
    master_telegram_user_id: int
    booking_id: int
    reason: str


class TelegramMasterDayOffUpsertRequest(BaseModel):
    master_telegram_user_id: int
    start_at: datetime
    end_at: datetime
    block_id: int | None = None


class TelegramMasterLunchUpdateRequest(BaseModel):
    master_telegram_user_id: int
    lunch_start: time
    lunch_end: time


class TelegramMasterManualBookingRequest(BaseModel):
    master_telegram_user_id: int
    client_name: str
    service_type: str
    slot_start: datetime


@app.get("/health")
@instrument_endpoint("GET", "/health")
def health() -> dict[str, str]:
    set_service_health(True)
    return {"status": "ok", "service": "bot-api"}


@app.get("/metrics")
@instrument_endpoint("GET", "/metrics")
def metrics() -> Response:
    content, content_type = render_metrics()
    return Response(content=content, media_type=content_type)


@app.post("/internal/auth/resolve-role")
@instrument_endpoint("POST", "/internal/auth/resolve-role")
def resolve_role(payload: ResolveRoleRequest) -> dict[str, str | None]:
    repository = RoleRepository(get_engine())
    role = repository.resolve_role(payload.telegram_user_id)
    return {"role": role}


@app.post("/internal/commands/authorize")
@instrument_endpoint("POST", "/internal/commands/authorize")
def authorize(payload: AuthorizeCommandRequest) -> dict[str, str | bool | None]:
    repository = RoleRepository(get_engine())
    role = repository.resolve_role(payload.telegram_user_id)
    decision = authorize_command(payload.command, role)

    if not decision.allowed:
        emit_event(
            "rbac_deny",
            telegram_user_id=payload.telegram_user_id,
            command=payload.command,
            resolved_role=role,
            message=decision.message,
        )

    return {
        "allowed": decision.allowed,
        "role": role,
        "message": decision.message,
    }


@app.get("/internal/booking/service-options")
@instrument_endpoint("GET", "/internal/booking/service-options")
def service_options() -> dict[str, list[dict[str, str]]]:
    return {"service_options": list_service_options()}


@app.post("/internal/availability/slots")
@instrument_endpoint("POST", "/internal/availability/slots")
def availability_slots(payload: AvailabilityRequest) -> dict[str, int | list[dict[str, str]]]:
    service = AvailabilityService(get_engine())
    slots = service.list_slots(master_id=payload.master_id, on_date=payload.date)
    return {
        "slot_minutes": 60,
        "slots": [
            {"start_at": slot.start_at.isoformat(), "end_at": slot.end_at.isoformat()}
            for slot in slots
        ],
    }


@app.post("/internal/booking/create")
@instrument_endpoint(
    "POST",
    "/internal/booking/create",
    booking_action="booking_create",
    outcome_key="created",
)
def create_booking(payload: CreateBookingRequest) -> dict[str, int | str | bool | None]:
    service = BookingService(get_engine())
    result = service.create_booking(
        master_id=payload.master_id,
        client_user_id=payload.client_user_id,
        service_type=payload.service_type,
        slot_start=payload.slot_start,
    )
    response = {
        "created": result.created,
        "booking_id": result.booking_id,
        "message": result.message,
    }
    emit_event(
        "booking_create",
        master_id=payload.master_id,
        client_user_id=payload.client_user_id,
        service_type=payload.service_type,
        slot_start=payload.slot_start.isoformat(),
        created=result.created,
        booking_id=result.booking_id,
    )
    return response


@app.get("/internal/telegram/client/booking-flow/start")
@instrument_endpoint("GET", "/internal/telegram/client/booking-flow/start")
def telegram_booking_flow_start() -> dict[str, object]:
    flow = TelegramBookingFlowService(get_engine())
    return flow.start()


@app.post("/internal/telegram/client/booking-flow/select-master")
@instrument_endpoint("POST", "/internal/telegram/client/booking-flow/select-master")
def telegram_booking_flow_select_master(payload: TelegramFlowMasterRequest) -> dict[str, object]:
    flow = TelegramBookingFlowService(get_engine())
    return flow.select_master(payload.master_id)


@app.post("/internal/telegram/client/booking-flow/select-service")
@instrument_endpoint("POST", "/internal/telegram/client/booking-flow/select-service")
def telegram_booking_flow_select_service(payload: TelegramFlowServiceRequest) -> dict[str, object]:
    flow = TelegramBookingFlowService(get_engine())
    return flow.select_service(master_id=payload.master_id, on_date=payload.date)


@app.post("/internal/telegram/client/booking-flow/confirm")
@instrument_endpoint(
    "POST",
    "/internal/telegram/client/booking-flow/confirm",
    booking_action="booking_flow_confirm",
    outcome_key="created",
)
def telegram_booking_flow_confirm(payload: TelegramFlowConfirmRequest) -> dict[str, object]:
    flow = TelegramBookingFlowService(get_engine())
    response = flow.confirm(
        client_telegram_user_id=payload.client_telegram_user_id,
        master_id=payload.master_id,
        service_type=payload.service_type,
        slot_start=payload.slot_start,
    )
    emit_event(
        "booking_flow_confirm",
        client_telegram_user_id=payload.client_telegram_user_id,
        master_id=payload.master_id,
        service_type=payload.service_type,
        slot_start=payload.slot_start.isoformat(),
        created=response.get("created"),
        booking_id=response.get("booking_id"),
    )
    return response


@app.post("/internal/telegram/client/booking-flow/cancel")
@instrument_endpoint(
    "POST",
    "/internal/telegram/client/booking-flow/cancel",
    booking_action="booking_flow_cancel_client",
    outcome_key="cancelled",
)
def telegram_booking_flow_cancel(payload: TelegramFlowCancelRequest) -> dict[str, object]:
    flow = TelegramBookingFlowService(get_engine())
    response = flow.cancel(
        client_telegram_user_id=payload.client_telegram_user_id,
        booking_id=payload.booking_id,
    )
    emit_event(
        "booking_flow_cancel_client",
        client_telegram_user_id=payload.client_telegram_user_id,
        booking_id=payload.booking_id,
        cancelled=response.get("cancelled"),
    )
    return response


@app.post("/internal/telegram/master/booking-flow/cancel")
@instrument_endpoint(
    "POST",
    "/internal/telegram/master/booking-flow/cancel",
    booking_action="booking_flow_cancel_master",
    outcome_key="cancelled",
)
def telegram_master_booking_flow_cancel(payload: TelegramFlowMasterCancelRequest) -> dict[str, object]:
    flow = TelegramBookingFlowService(get_engine())
    response = flow.cancel_by_master(
        master_telegram_user_id=payload.master_telegram_user_id,
        booking_id=payload.booking_id,
        reason=payload.reason,
    )
    emit_event(
        "booking_flow_cancel_master",
        master_telegram_user_id=payload.master_telegram_user_id,
        booking_id=payload.booking_id,
        reason_provided=bool(payload.reason.strip()),
        cancelled=response.get("cancelled"),
    )
    return response


@app.post("/internal/telegram/master/schedule/day-off")
@instrument_endpoint(
    "POST",
    "/internal/telegram/master/schedule/day-off",
    booking_action="schedule_day_off",
    outcome_key="applied",
)
def telegram_master_schedule_day_off(payload: TelegramMasterDayOffUpsertRequest) -> dict[str, object]:
    service = MasterScheduleService(get_engine())
    result = service.upsert_day_off(
        master_telegram_user_id=payload.master_telegram_user_id,
        command=MasterDayOffCommand(
            start_at=payload.start_at,
            end_at=payload.end_at,
            block_id=payload.block_id,
        ),
    )
    response = {
        "applied": result.applied,
        "created": result.created,
        "block_id": result.block_id,
        "message": result.message,
    }
    emit_event(
        "schedule_day_off_upsert",
        master_telegram_user_id=payload.master_telegram_user_id,
        block_id=result.block_id,
        applied=result.applied,
        created=result.created,
    )
    return response


@app.post("/internal/telegram/master/schedule/lunch")
@instrument_endpoint(
    "POST",
    "/internal/telegram/master/schedule/lunch",
    booking_action="schedule_lunch_update",
    outcome_key="applied",
)
def telegram_master_schedule_lunch(payload: TelegramMasterLunchUpdateRequest) -> dict[str, object]:
    service = MasterScheduleService(get_engine())
    result = service.update_lunch_break(
        master_telegram_user_id=payload.master_telegram_user_id,
        command=MasterLunchBreakCommand(
            lunch_start=payload.lunch_start,
            lunch_end=payload.lunch_end,
        ),
    )
    response = {
        "applied": result.applied,
        "message": result.message,
    }
    emit_event(
        "schedule_lunch_update",
        master_telegram_user_id=payload.master_telegram_user_id,
        lunch_start=payload.lunch_start.isoformat(),
        lunch_end=payload.lunch_end.isoformat(),
        applied=result.applied,
    )
    return response


@app.post("/internal/telegram/master/schedule/manual-booking")
@instrument_endpoint(
    "POST",
    "/internal/telegram/master/schedule/manual-booking",
    booking_action="schedule_manual_booking",
    outcome_key="applied",
)
def telegram_master_schedule_manual_booking(payload: TelegramMasterManualBookingRequest) -> dict[str, object]:
    service = MasterScheduleService(get_engine())
    result = service.create_manual_booking(
        master_telegram_user_id=payload.master_telegram_user_id,
        command=MasterManualBookingCommand(
            client_name=payload.client_name,
            service_type=payload.service_type,
            slot_start=payload.slot_start,
        ),
    )
    response = {
        "applied": result.applied,
        "booking_id": result.booking_id,
        "message": result.message,
    }
    emit_event(
        "schedule_manual_booking",
        master_telegram_user_id=payload.master_telegram_user_id,
        service_type=payload.service_type,
        slot_start=payload.slot_start.isoformat(),
        applied=result.applied,
        booking_id=result.booking_id,
    )
    return response
