from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import UTC, datetime
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

SERVICE_NAME = "bot-api"

_SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "authorization",
    "api_key",
    "database_url",
)
_REDACTED = "[REDACTED]"
_METRICS_LOCK = threading.Lock()
_REQUEST_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

_REQUESTS_TOTAL: dict[tuple[str, str, str], float] = {}
_REQUEST_LATENCY: dict[tuple[str, str], dict[str, float | list[float]]] = {}
_BOOKING_OUTCOMES_TOTAL: dict[tuple[str, str], float] = {}
_ABUSE_OUTCOMES_TOTAL: dict[tuple[str, str], float] = {}
_SERVICE_HEALTH = 1.0


def _coerce_buckets(value: float | list[float]) -> list[float]:
    if isinstance(value, list):
        return value
    raise TypeError("Invalid latency buckets payload; expected list[float].")


def _is_sensitive_key(key: str) -> bool:
    key_normalized = key.strip().lower()
    if key_normalized.endswith("_configured"):
        return False
    return any(part in key_normalized for part in _SENSITIVE_KEY_PARTS)


def _redact_value(value: Any, key: str | None = None) -> Any:
    if key and _is_sensitive_key(key):
        return _REDACTED

    if isinstance(value, dict):
        return {item_key: _redact_value(item_value, item_key) for item_key, item_value in value.items()}

    if isinstance(value, list):
        return [_redact_value(item) for item in value]

    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)

    if isinstance(value, str):
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if token and token in value:
            return value.replace(token, _REDACTED)
        return value

    return value


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def emit_event(event: str, **fields: Any) -> None:
    logger = logging.getLogger("bot_api")
    payload = {
        "event": event,
        "service": SERVICE_NAME,
        "ts": datetime.now(UTC).isoformat(),
    }
    payload.update(fields)
    logger.info(json.dumps(_redact_value(payload), ensure_ascii=False))


def set_service_health(healthy: bool) -> None:
    global _SERVICE_HEALTH
    with _METRICS_LOCK:
        _SERVICE_HEALTH = 1.0 if healthy else 0.0


def observe_request(method: str, path: str, status_code: str, duration_seconds: float) -> None:
    key_requests = (method, path, status_code)
    key_latency = (method, path)

    with _METRICS_LOCK:
        _REQUESTS_TOTAL[key_requests] = _REQUESTS_TOTAL.get(key_requests, 0.0) + 1.0

        series = _REQUEST_LATENCY.get(key_latency)
        if series is None:
            series = {
                "count": 0.0,
                "sum": 0.0,
                "buckets": [0.0] * (len(_REQUEST_LATENCY_BUCKETS) + 1),
            }
            _REQUEST_LATENCY[key_latency] = series

        series["count"] = float(series["count"]) + 1.0
        series["sum"] = float(series["sum"]) + duration_seconds

        buckets = _coerce_buckets(series["buckets"])
        for index, boundary in enumerate(_REQUEST_LATENCY_BUCKETS):
            if duration_seconds <= boundary:
                buckets[index] += 1.0
        buckets[-1] += 1.0


def observe_booking_outcome(action: str, success: bool) -> None:
    outcome = "success" if success else "failure"
    key = (action, outcome)

    with _METRICS_LOCK:
        _BOOKING_OUTCOMES_TOTAL[key] = _BOOKING_OUTCOMES_TOTAL.get(key, 0.0) + 1.0


def observe_abuse_outcome(path: str, allowed: bool) -> None:
    outcome = "allow" if allowed else "deny"
    key = (path, outcome)

    with _METRICS_LOCK:
        _ABUSE_OUTCOMES_TOTAL[key] = _ABUSE_OUTCOMES_TOTAL.get(key, 0.0) + 1.0


def render_metrics() -> tuple[bytes, str]:
    lines: list[str] = []

    with _METRICS_LOCK:
        lines.append("# HELP bot_api_service_health Service health status (1=healthy, 0=unhealthy).")
        lines.append("# TYPE bot_api_service_health gauge")
        lines.append(f"bot_api_service_health {_SERVICE_HEALTH:.1f}")

        lines.append("# HELP bot_api_requests_total HTTP requests handled by the bot API.")
        lines.append("# TYPE bot_api_requests_total counter")
        for (method, path, status_code), value in sorted(_REQUESTS_TOTAL.items()):
            lines.append(
                "bot_api_requests_total"
                f'{{method="{_escape_label(method)}",path="{_escape_label(path)}",status_code="{_escape_label(status_code)}"}} {value:.1f}'
            )

        lines.append("# HELP bot_api_request_latency_seconds HTTP request latency in seconds.")
        lines.append("# TYPE bot_api_request_latency_seconds histogram")
        for (method, path), series in sorted(_REQUEST_LATENCY.items()):
            buckets = _coerce_buckets(series["buckets"])
            count = float(series["count"])
            total = float(series["sum"])
            for index, boundary in enumerate(_REQUEST_LATENCY_BUCKETS):
                lines.append(
                    "bot_api_request_latency_seconds_bucket"
                    f'{{method="{_escape_label(method)}",path="{_escape_label(path)}",le="{boundary}"}} {buckets[index]:.1f}'
                )
            lines.append(
                "bot_api_request_latency_seconds_bucket"
                f'{{method="{_escape_label(method)}",path="{_escape_label(path)}",le="+Inf"}} {buckets[-1]:.1f}'
            )
            lines.append(
                "bot_api_request_latency_seconds_sum"
                f'{{method="{_escape_label(method)}",path="{_escape_label(path)}"}} {total:.6f}'
            )
            lines.append(
                "bot_api_request_latency_seconds_count"
                f'{{method="{_escape_label(method)}",path="{_escape_label(path)}"}} {count:.1f}'
            )

        lines.append("# HELP bot_api_booking_outcomes_total Outcomes for booking and schedule write operations.")
        lines.append("# TYPE bot_api_booking_outcomes_total counter")
        for (action, outcome), value in sorted(_BOOKING_OUTCOMES_TOTAL.items()):
            lines.append(
                "bot_api_booking_outcomes_total"
                f'{{action="{_escape_label(action)}",outcome="{_escape_label(outcome)}"}} {value:.1f}'
            )

        lines.append("# HELP bot_api_abuse_outcomes_total Outcomes for Telegram abuse-throttling checks.")
        lines.append("# TYPE bot_api_abuse_outcomes_total counter")
        for (path, outcome), value in sorted(_ABUSE_OUTCOMES_TOTAL.items()):
            lines.append(
                "bot_api_abuse_outcomes_total"
                f'{{path="{_escape_label(path)}",outcome="{_escape_label(outcome)}"}} {value:.1f}'
            )

    payload = "\n".join(lines) + "\n"
    return payload.encode("utf-8"), "text/plain; version=0.0.4; charset=utf-8"


def instrument_endpoint(
    method: str,
    path: str,
    booking_action: str | None = None,
    outcome_key: str | None = None,
) -> Callable[[F], F]:
    method_value = method.upper()

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            status_code = "200"
            started_at = time.perf_counter()

            try:
                response = func(*args, **kwargs)
            except Exception:
                status_code = "500"
                raise
            finally:
                observe_request(
                    method=method_value,
                    path=path,
                    status_code=status_code,
                    duration_seconds=time.perf_counter() - started_at,
                )

            if booking_action and outcome_key and isinstance(response, dict):
                observe_booking_outcome(booking_action, response.get(outcome_key) is True)

            return response

        return wrapper  # type: ignore[return-value]

    return decorator
