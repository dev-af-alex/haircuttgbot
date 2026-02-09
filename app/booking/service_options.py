from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

SERVICE_OPTION_HAIRCUT = "haircut"
SERVICE_OPTION_BEARD = "beard"
SERVICE_OPTION_HAIRCUT_BEARD = "haircut_beard"

SERVICE_OPTION_CODES = (
    SERVICE_OPTION_HAIRCUT,
    SERVICE_OPTION_BEARD,
    SERVICE_OPTION_HAIRCUT_BEARD,
)

SERVICE_OPTION_LABELS_RU = {
    SERVICE_OPTION_HAIRCUT: "Стрижка",
    SERVICE_OPTION_BEARD: "Борода",
    SERVICE_OPTION_HAIRCUT_BEARD: "Стрижка + борода",
}

_SERVICE_OPTION_DEFAULT_DURATIONS = {
    SERVICE_OPTION_HAIRCUT: 30,
    SERVICE_OPTION_BEARD: 30,
    SERVICE_OPTION_HAIRCUT_BEARD: 60,
}


def validate_duration_minutes(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("duration_minutes must be an integer")
    if value <= 0:
        raise ValueError("duration_minutes must be greater than zero")
    return value


SERVICE_OPTION_DURATION_MINUTES = {
    code: validate_duration_minutes(duration)
    for code, duration in _SERVICE_OPTION_DEFAULT_DURATIONS.items()
}

DEFAULT_SLOT_DURATION_MINUTES = 60
DEFAULT_SLOT_STEP_MINUTES = 30


def list_service_options() -> list[dict[str, str]]:
    return [
        {"code": code, "label": SERVICE_OPTION_LABELS_RU[code]}
        for code in SERVICE_OPTION_CODES
    ]


def list_service_catalog_defaults() -> list[dict[str, str | int]]:
    return [
        {
            "code": code,
            "label_ru": SERVICE_OPTION_LABELS_RU[code],
            "duration_minutes": SERVICE_OPTION_DURATION_MINUTES[code],
        }
        for code in SERVICE_OPTION_CODES
    ]


def resolve_service_duration_minutes(
    service_type: str,
    *,
    connection: Connection | None = None,
) -> int | None:
    if service_type not in SERVICE_OPTION_CODES:
        return None

    if connection is not None:
        try:
            row = connection.execute(
                text(
                    """
                    SELECT duration_minutes
                    FROM services
                    WHERE code = :code
                      AND is_active = true
                    """
                ),
                {"code": service_type},
            ).mappings().first()
        except SQLAlchemyError:
            row = None
        if row is not None:
            duration = _extract_duration_minutes(row)
            if duration is not None:
                return duration

    return SERVICE_OPTION_DURATION_MINUTES.get(service_type)


def _extract_duration_minutes(row: Mapping[str, object]) -> int | None:
    raw = row.get("duration_minutes")
    if not isinstance(raw, int) or isinstance(raw, bool):
        return None
    return validate_duration_minutes(raw)
