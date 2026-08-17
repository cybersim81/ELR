import importlib

from sqlalchemy.orm import Session


def test_database_uses_database_url_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    import app.persistence.database as database

    database = importlib.reload(database)

    assert str(database.engine.url) == "sqlite:///:memory:"


def test_session_factory_creates_bound_session(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    import app.persistence.database as database

    database = importlib.reload(database)

    session = database.SessionFactory()

    try:
        assert isinstance(session, Session)
        assert session.bind is database.engine
    finally:
        session.close()
