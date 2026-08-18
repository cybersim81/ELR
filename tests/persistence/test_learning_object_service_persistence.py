import pytest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.persistence.models.audit_record_model import AuditRecordModel
from app.persistence.models.learning_object_model import LearningObjectModel
from app.persistence.models.version_model import VersionModel


def test_approve_persists_version_and_audit(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    from app.persistence.models.base import Base
    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.knowledge_category_model import (
        KnowledgeCategoryModel,
    )
    from app.persistence.transaction import transaction
    from app.persistence.wiring import create_learning_object_service
    from app.domain.entities.knowledge_statement import KnowledgeStatement

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionFactory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )

    session = SessionFactory()

    try:
        anchor_id = uuid4()
        category_id = uuid4()

        session.add(
            AnchorModel(
                id=anchor_id,
                content="Test anchor",
                type="text",
                created_at=datetime.now(timezone.utc),
            )
        )

        session.add(
            KnowledgeCategoryModel(
                id=category_id,
                name="Test category",
            )
        )

        session.commit()

        service, _ = create_learning_object_service(session)

        learning_object = service.create_candidate(
            anchor_id=anchor_id,
            statement=KnowledgeStatement(
                text="Test knowledge",
                language="en",
            ),
            category_id=category_id,
            actor="test",
        )

        service.submit_for_review(
            learning_object.id,
            actor="test",
        )

        with transaction(session):
            approved = service.approve(
                learning_object.id,
                actor="reviewer",
            )

        assert approved.state.value == "Active"

        model = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert model is not None
        assert model.state == "Active"

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

        assert len(audits) == 3
        assert [
            audit.event_type
            for audit in audits
        ] == [
            "LearningObjectCreated",
            "LearningObjectSubmitted",
            "LearningObjectApproved",
        ]

        assert audits[-1].actor == "reviewer"

    finally:
        session.close()
        engine.dispose()


def test_approve_rollback_removes_version_and_audit(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    from app.persistence.models.base import Base
    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.knowledge_category_model import (
        KnowledgeCategoryModel,
    )
    from app.persistence.transaction import transaction
    from app.persistence.wiring import create_learning_object_service
    from app.domain.entities.knowledge_statement import KnowledgeStatement

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionFactory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )

    session = SessionFactory()

    try:
        anchor_id = uuid4()
        category_id = uuid4()

        session.add(
            AnchorModel(
                id=anchor_id,
                content="Test anchor",
                type="text",
                created_at=datetime.now(timezone.utc),
            )
        )

        session.add(
            KnowledgeCategoryModel(
                id=category_id,
                name="Test category",
            )
        )

        session.commit()

        service, _ = create_learning_object_service(session)

        learning_object = service.create_candidate(
            anchor_id=anchor_id,
            statement=KnowledgeStatement(
                text="Test knowledge",
                language="en",
            ),
            category_id=category_id,
            actor="test",
        )

        service.submit_for_review(
            learning_object.id,
            actor="test",
        )

        with pytest.raises(RuntimeError, match="boom"):
            with transaction(session):
                service.approve(
                    learning_object.id,
                    actor="reviewer",
                )
                raise RuntimeError("boom")

        session.expire_all()

        model = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert model is not None
        assert model.state == "Proposed"

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

        assert len(audits) == 2
        assert [
            audit.event_type
            for audit in audits
        ] == [
            "LearningObjectCreated",
            "LearningObjectSubmitted",
        ]

    finally:
        session.close()
        engine.dispose()
