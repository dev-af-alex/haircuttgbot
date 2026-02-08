from __future__ import annotations

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


def list_service_options() -> list[dict[str, str]]:
    return [
        {"code": code, "label": SERVICE_OPTION_LABELS_RU[code]}
        for code in SERVICE_OPTION_CODES
    ]
