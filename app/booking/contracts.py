from __future__ import annotations

BOOKING_STATUS_ACTIVE = "active"
BOOKING_STATUS_CANCELLED_BY_CLIENT = "cancelled_by_client"
BOOKING_STATUS_CANCELLED_BY_MASTER = "cancelled_by_master"
BOOKING_STATUS_COMPLETED = "completed"

BOOKING_STATUS_TRANSITIONS = {
    BOOKING_STATUS_ACTIVE: {
        BOOKING_STATUS_CANCELLED_BY_CLIENT,
        BOOKING_STATUS_CANCELLED_BY_MASTER,
        BOOKING_STATUS_COMPLETED,
    }
}

BOOKING_CANCELLATION_REASON_REQUIRED = {
    BOOKING_STATUS_CANCELLED_BY_CLIENT: False,
    BOOKING_STATUS_CANCELLED_BY_MASTER: True,
}


def can_transition_booking_status(*, current_status: str, target_status: str) -> bool:
    return target_status in BOOKING_STATUS_TRANSITIONS.get(current_status, set())


def is_cancellation_reason_required(*, target_status: str) -> bool:
    return BOOKING_CANCELLATION_REASON_REQUIRED.get(target_status, False)
