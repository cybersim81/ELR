import importlib
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


def test_approve_persists_version_and_audit(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite://",
    )

    import app.persistence.database as database

    database = importlib.reload(database)

    from app.persistence.models.base import Base
    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.audit_record_model import AuditRecordModel
    from app.persistence.models.knowledge_category_model import (
        KnowledgeCategoryModel,
    )
    from app.persistence.models.learning_object_model import (
        LearningObjectModel,
    )
    from app.persistence.models.learning_object_value_models import (
        LearningObjectExampleModel,
        LearningObjectNoteModel,
    )
    from app.persistence.models.version_model import VersionModel

    from app.domain.entities.knowledge_statement import KnowledgeStatement
    from app.persistence.transaction import transaction
    from app.persistence.wiring import create_learning_object_service

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    SessionFactory = database.sessionmaker(
        bind=engine,
        class_=database.Session,
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
                created_at=__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ),
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
                text="Test knowledge statement",
                language="en",
            ),
            category_id=category_id,
            actor="creator",
        )

        session.commit()

        service.submit_for_review(
            learning_object.id,
            actor="producer",
        )

        session.commit()

        with transaction(session):
            approved = service.approve(
                learning_object.id,
                actor="reviewer",
            )

        assert approved.state.value == "Active"

        session.expire_all()

        persisted = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert persisted is not None
        assert persisted.state == "Active"

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
        assert versions[0].snapshot["state"] == "Active"

        audits = (
            session.query(AuditRecordModel)
            .filter(
                AuditRecordModel.entity_id
                == learning_object.id
            )
            .order_by(AuditRecordModel.timestamp.asc())
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
        assert audits[-1].metadata_ == {"version": 1}

    finally:
        session.close()
        engine.dispose()


def test_approve_rolls_back_learning_object_and_version_on_audit_error(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite://",
    )

    import importlib

    import app.persistence.database as database

    database = importlib.reload(database)

    from app.persistence.models.base import Base
    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.audit_record_model import AuditRecordModel
    from app.persistence.models.knowledge_category_model import (
        KnowledgeCategoryModel,
    )
    from app.persistence.models.learning_object_model import (
        LearningObjectModel,
    )
    from app.persistence.models.version_model import VersionModel

    from app.domain.entities.knowledge_statement import KnowledgeStatement
    from app.persistence.transaction import transaction
    from app.persistence.wiring import create_learning_object_service

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    SessionFactory = database.sessionmaker(
        bind=engine,
        class_=database.Session,
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
                created_at=__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ),
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
                text="Test knowledge statement",
                language="en",
            ),
            category_id=category_id,
            actor="creator",
        )

        session.commit()

        service.submit_for_review(
            learning_object.id,
            actor="producer",
        )

        session.commit()

        def fail_audit(*args, **kwargs) -> None:
            raise RuntimeError("audit failure")

        monkeypatch.setattr(
            service.audit_repository,
            "record",
            fail_audit,
        )

        try:
            with transaction(session):
                service.approve(
                    learning_object.id,
                    actor="reviewer",
                )
        except RuntimeError as exc:
            assert str(exc) == "audit failure"
        else:
            raise AssertionError(
                "approve() should have raised RuntimeError"
            )

        session.expire_all()

        persisted = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert persisted is not None
        assert persisted.state == "Proposed"

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
            .order_by(AuditRecordModel.timestamp.asc())
            .all()
        )

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
