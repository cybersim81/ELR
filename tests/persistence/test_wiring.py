from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.persistence.wiring import create_learning_object_service
from app.persistence.repositories.audit_repository import (
    SQLAlchemyAuditRepository,
)
from app.persistence.repositories.learning_object_repository import (
    SQLAlchemyLearningObjectRepository,
)
from app.persistence.repositories.version_repository import (
    SQLAlchemyVersionRepository,
)


def test_create_learning_object_service_creates_session() -> None:
    service, session = create_learning_object_service()

    try:
        assert service is not None
        assert isinstance(session, Session)
        assert session.bind is not None
    finally:
        session.close()


def test_create_learning_object_service_uses_provided_session() -> None:
    engine = create_engine("sqlite:///:memory:")
    test_session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )
    session = test_session_factory()

    try:
        service, returned_session = create_learning_object_service(session)

        assert returned_session is session

        assert isinstance(
            service.learning_object_repository,
            SQLAlchemyLearningObjectRepository,
        )
        assert isinstance(
            service.version_repository,
            SQLAlchemyVersionRepository,
        )
        assert isinstance(
            service.audit_repository,
            SQLAlchemyAuditRepository,
        )

        assert service.learning_object_repository.session is session
        assert service.version_repository.session is session
        assert service.audit_repository.session is session
    finally:
        session.close()
        engine.dispose()
