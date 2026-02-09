from app.main import _resolve_telegram_runtime_policy, _resolve_telegram_updates_mode


def test_resolve_telegram_updates_mode_defaults_to_polling() -> None:
    assert _resolve_telegram_updates_mode(None) == "polling"
    assert _resolve_telegram_updates_mode("") == "polling"
    assert _resolve_telegram_updates_mode("  ") == "polling"


def test_resolve_telegram_updates_mode_disables_invalid_values() -> None:
    assert _resolve_telegram_updates_mode("webhook") == "disabled"
    assert _resolve_telegram_updates_mode("abc") == "disabled"


def test_resolve_telegram_runtime_policy_requires_token_for_polling() -> None:
    assert _resolve_telegram_runtime_policy(raw_mode="polling", bot_token="") == {
        "mode": "polling",
        "start_polling": False,
        "reason": "missing_token",
    }

    assert _resolve_telegram_runtime_policy(raw_mode="polling", bot_token="token") == {
        "mode": "polling",
        "start_polling": True,
        "reason": "enabled",
    }


def test_resolve_telegram_runtime_policy_can_be_disabled() -> None:
    assert _resolve_telegram_runtime_policy(raw_mode="disabled", bot_token="token") == {
        "mode": "disabled",
        "start_polling": False,
        "reason": "mode_disabled",
    }
