from app.main import health


def test_health_contract() -> None:
    payload = health()
    assert payload == {"status": "ok", "service": "bot-api"}
