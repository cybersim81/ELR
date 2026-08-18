import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.persistence import transaction as transaction_module
from app.persistence.wiring import create_learning_object_service


def test_transaction_and_wiring_share_the_same_session(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )

    session = session_factory()

    try:
        with transaction_module.transaction(session) as transaction_session:
            service, returned_session = create_learning_object_service(
                transaction_session
            )

            assert returned_session is transaction_session

            assert service.learning_object_repository._session is (
                transaction_session
            )
            assert service.version_repository._session is (
                transaction_session
            )
            assert service.audit_repository._session is (
                transaction_session
            )
    finally:
        session.close()
        engine.dispose()


def test_transaction_wiring_rolls_back_on_error(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )

    session = session_factory()

    try:
        with pytest.raises(RuntimeError, match="boom"):
            with transaction_module.transaction(session) as transaction_session:
                service, _ = create_learning_object_service(
                    transaction_session
                )

                assert service is not None

                transaction_session.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )

                raise RuntimeError("boom")

        assert session.is_active
    finally:
        session.close()
        engine.dispose()
