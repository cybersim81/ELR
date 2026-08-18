import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def test_transaction_commits_on_success(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    from app.persistence.transaction import transaction

    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine, class_=Session)
    session = session_factory()

    try:
        with transaction(session):
            session.execute(text("SELECT 1"))

        assert session.is_active
    finally:
        session.close()
        engine.dispose()


def test_transaction_rolls_back_on_error(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    from app.persistence.transaction import transaction

    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine, class_=Session)
    session = session_factory()

    try:
        with pytest.raises(RuntimeError, match="boom"):
            with transaction(session):
                session.execute(text("SELECT 1"))
                raise RuntimeError("boom")

        assert session.is_active
    finally:
        session.close()
        engine.dispose()


def test_transaction_closes_owned_session(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    from app.persistence.transaction import transaction

    engine = create_engine("sqlite:///:memory:")

    class TrackingSession(Session):
        closed = False

        def close(self) -> None:
            self.closed = True
            super().close()

    tracking_factory = sessionmaker(
        bind=engine,
        class_=TrackingSession,
    )

    session = tracking_factory()

    try:
        with transaction(session):
            pass

        assert session.closed
    finally:
        if not session.closed:
            session.close()
        engine.dispose()
