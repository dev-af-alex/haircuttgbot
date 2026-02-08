from sqlalchemy import create_engine, text

from app.auth.rbac import authorize_command
from app.auth.repository import RoleRepository


def test_authorize_master_command_allowed() -> None:
    decision = authorize_command("master:schedule", "Master")
    assert decision.allowed is True


def test_authorize_master_command_forbidden_for_client() -> None:
    decision = authorize_command("master:schedule", "Client")
    assert decision.allowed is False


def test_authorize_unknown_user() -> None:
    decision = authorize_command("client:book", None)
    assert decision.allowed is False


def test_role_repository_resolve_role_known_and_unknown() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)"))
        conn.execute(
            text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, telegram_user_id BIGINT UNIQUE NOT NULL, role_id INTEGER NOT NULL)"
            )
        )
        conn.execute(text("INSERT INTO roles (id, name) VALUES (1, 'Client'), (2, 'Master')"))
        conn.execute(text("INSERT INTO users (telegram_user_id, role_id) VALUES (1000001, 2)"))

    repository = RoleRepository(engine)

    assert repository.resolve_role(1000001) == "Master"
    assert repository.resolve_role(9999999) is None
