import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.knowledge_statement import KnowledgeStatement
from app.domain.entities.learning_object import LearningObject
from app.persistence.models.audit_record_model import AuditRecordModel
from app.persistence.models.learning_object_model import LearningObjectModel
from app.persistence.models.version_model import VersionModel


def test_approve_persists_learning_object_version_and_audit(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    from app.persistence.database import Base
    from app.persistence.transaction import transaction
    from app.persistence.wiring import create_learning_object_service

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )

    session = session_factory()

    try:
        service, _ = create_learning_object_service(session)

        learning_object = LearningObject(
            anchor_id=__import__("uuid").uuid4(),
            statement=KnowledgeStatement(
                text="Test knowledge",
                language="en",
            ),
            category_id=__import__("uuid").uuid4(),
        )

        with transaction(session):
            service.learning_object_repository.save(
                learning_object
            )

        session.expire_all()

        proposed = service.get(learning_object.id)

        assert proposed.id == learning_object.id

        with transaction(session):
            approved = service.approve(
                learning_object.id,
                actor="test",
            )

        assert approved.state.value == "active"

        persisted_learning_object = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert persisted_learning_object is not None
        assert persisted_learning_object.state == "active"

        versions = (
            session.query(VersionModel)
            .filter(
                VersionModel.learning_object_id
                == learning_object.id
            )
            .all()
        )

        assert len(versions) == 1
        assert versions[0].number == 1

        audits = (
            session.query(AuditRecordModel)
            .filter(
                AuditRecordModel.entity_id
                == learning_object.id
            )
            .all()
        )

        assert len(audits) == 1
        assert audits[0].event_type == "LearningObjectApproved"
        assert audits[0].actor == "test"
        assert audits[0].metadata_ == {"version": 1}

    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_approve_rolls_back_all_persistence_on_error(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    from app.persistence.database import Base
    from app.persistence.transaction import transaction
    from app.persistence.wiring import create_learning_object_service

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )

    session = session_factory()

    try:
        service, _ = create_learning_object_service(session)

        learning_object = LearningObject(
            anchor_id=__import__("uuid").uuid4(),
            statement=KnowledgeStatement(
                text="Test knowledge",
                language="en",
            ),
            category_id=__import__("uuid").uuid4(),
        )

        with transaction(session):
            service.learning_object_repository.save(
                learning_object
            )

        with pytest.raises(RuntimeError, match="boom"):
            with transaction(session):
                service.approve(
                    learning_object.id,
                    actor="test",
                )
                raise RuntimeError("boom")

        session.expire_all()

        persisted_learning_object = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert persisted_learning_object is not None
        assert persisted_learning_object.state != "active"

        versions = (
            session.query(VersionModel)
            .filter(
                VersionModel.learning_object_id
                == learning_object.id
            )
            .all()
        )

        assert versions == []

        audits = (
            session.query(AuditRecordModel)
            .filter(
                AuditRecordModel.entity_id
                == learning_object.id
            )
            .all()
        )

        assert audits == []

    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
