import json
import logging
import os
from datetime import date, datetime

from aiogram import Dispatcher
from fastapi import FastAPI
from pydantic import BaseModel

from app.auth import RoleRepository, authorize_command
from app.booking import AvailabilityService, BookingService, list_service_options
from app.db.session import get_engine

LOGGER = logging.getLogger("bot_api")
logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="haircuttgbot-api", version="0.1.0")


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


@app.on_event("startup")
def on_startup() -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Keep aiogram integration point present in runtime skeleton.
    _dispatcher = Dispatcher()
    _ = _dispatcher

    LOGGER.info(
        json.dumps(
            {
                "event": "startup",
                "service": "bot-api",
                "telegram_token_configured": bool(bot_token),
            }
        )
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "bot-api"}


@app.post("/internal/auth/resolve-role")
def resolve_role(payload: ResolveRoleRequest) -> dict[str, str | None]:
    repository = RoleRepository(get_engine())
    role = repository.resolve_role(payload.telegram_user_id)
    return {"role": role}


@app.post("/internal/commands/authorize")
def authorize(payload: AuthorizeCommandRequest) -> dict[str, str | bool | None]:
    repository = RoleRepository(get_engine())
    role = repository.resolve_role(payload.telegram_user_id)
    decision = authorize_command(payload.command, role)

    if not decision.allowed:
        LOGGER.info(
            json.dumps(
                {
                    "event": "rbac_deny",
                    "telegram_user_id": payload.telegram_user_id,
                    "command": payload.command,
                    "resolved_role": role,
                    "message": decision.message,
                }
            )
        )

    return {
        "allowed": decision.allowed,
        "role": role,
        "message": decision.message,
    }


@app.get("/internal/booking/service-options")
def service_options() -> dict[str, list[dict[str, str]]]:
    return {"service_options": list_service_options()}


@app.post("/internal/availability/slots")
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
def create_booking(payload: CreateBookingRequest) -> dict[str, int | str | bool | None]:
    service = BookingService(get_engine())
    result = service.create_booking(
        master_id=payload.master_id,
        client_user_id=payload.client_user_id,
        service_type=payload.service_type,
        slot_start=payload.slot_start,
    )
    return {
        "created": result.created,
        "booking_id": result.booking_id,
        "message": result.message,
    }
