import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from uuid import uuid4

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

    from app.persistence.models.base import Base
    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.category_model import CategoryModel
    from app.persistence.transaction import transaction
    from app.persistence.wiring import create_learning_object_service
    from app.domain.entities.knowledge_statement import KnowledgeStatement
    from app.domain.entities.learning_object import LearningObject

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )
    session = session_factory()

    try:
        anchor_id = uuid4()
        category_id = uuid4()

        session.add(
            AnchorModel(
                id=anchor_id,
            )
        )
        session.add(
            CategoryModel(
                id=category_id,
            )
        )
        session.commit()

        service, _ = create_learning_object_service(session)

        learning_object = LearningObject(
            anchor_id=anchor_id,
            statement=KnowledgeStatement(
                text="Test knowledge",
                language="en",
            ),
            category_id=category_id,
        )

        with transaction(session):
            service.learning_object_repository.save(
                learning_object
            )

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
        engine.dispose()


def test_approve_rolls_back_all_persistence_on_error(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    from app.persistence.models.base import Base
    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.category_model import CategoryModel
    from app.persistence.transaction import transaction
    from app.persistence.wiring import create_learning_object_service
    from app.domain.entities.knowledge_statement import KnowledgeStatement
    from app.domain.entities.learning_object import LearningObject

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )
    session = session_factory()

    try:
        anchor_id = uuid4()
        category_id = uuid4()

        session.add(
            AnchorModel(
                id=anchor_id,
            )
        )
        session.add(
            CategoryModel(
                id=category_id,
            )
        )
        session.commit()

        service, _ = create_learning_object_service(session)

        learning_object = LearningObject(
            anchor_id=anchor_id,
            statement=KnowledgeStatement(
                text="Test knowledge",
                language="en",
            ),
            category_id=category_id,
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

                session.execute(text("SELECT 1"))

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
        engine.dispose()
