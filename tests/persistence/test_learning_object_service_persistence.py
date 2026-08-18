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


def test_update_knowledge_persists_new_version_and_audit(
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
                text="Original knowledge statement",
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
            service.approve(
                learning_object.id,
                actor="reviewer",
            )

        session.expire_all()

        updated_statement = KnowledgeStatement(
            text="Updated knowledge statement",
            language="en",
        )

        with transaction(session):
            updated = service.update_knowledge(
                learning_object.id,
                updated_statement,
                actor="editor",
            )

        assert updated.state.value == "Active"
        assert updated.statement.text == "Updated knowledge statement"
        assert updated.statement.language == "en"

        session.expire_all()

        persisted = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert persisted is not None
        assert persisted.state == "Active"
        assert persisted.statement_text == "Updated knowledge statement"
        assert persisted.statement_language == "en"

        versions = (
            session.query(VersionModel)
            .filter(
                VersionModel.learning_object_id
                == learning_object.id
            )
            .order_by(VersionModel.number.asc())
            .all()
        )

        assert len(versions) == 2

        assert versions[0].number == 1
        assert (
            versions[0].snapshot["statement"]["text"]
            == "Original knowledge statement"
        )

        assert versions[1].number == 2
        assert (
            versions[1].snapshot["statement"]["text"]
            == "Updated knowledge statement"
        )
        assert (
            versions[1].snapshot["statement"]["language"]
            == "en"
        )
        assert versions[1].snapshot["state"] == "Active"

        audits = (
            session.query(AuditRecordModel)
            .filter(
                AuditRecordModel.entity_id
                == learning_object.id
            )
            .order_by(AuditRecordModel.timestamp.asc())
            .all()
        )

        assert len(audits) == 4

        assert [
            audit.event_type
            for audit in audits
        ] == [
            "LearningObjectCreated",
            "LearningObjectSubmitted",
            "LearningObjectApproved",
            "LearningObjectUpdated",
        ]

        assert audits[-1].actor == "editor"
        assert audits[-1].metadata_ == {"version": 2}

    finally:
        session.close()
        engine.dispose()


def test_update_knowledge_rolls_back_when_audit_fails(
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
                text="Original knowledge statement",
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
            service.approve(
                learning_object.id,
                actor="reviewer",
            )

        session.expire_all()

        original = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert original is not None
        assert original.state == "Active"
        assert original.statement_text == "Original knowledge statement"
        assert original.statement_language == "en"

        versions_before = (
            session.query(VersionModel)
            .filter(
                VersionModel.learning_object_id
                == learning_object.id
            )
            .order_by(VersionModel.number.asc())
            .all()
        )

        assert len(versions_before) == 1
        assert versions_before[0].number == 1
        assert (
            versions_before[0].snapshot["statement"]["text"]
            == "Original knowledge statement"
        )

        def fail_audit(*args, **kwargs) -> None:
            raise RuntimeError("audit failure")

        monkeypatch.setattr(
            service.audit_repository,
            "record",
            fail_audit,
        )

        try:
            with transaction(session):
                service.update_knowledge(
                    learning_object.id,
                    KnowledgeStatement(
                        text="Updated knowledge statement",
                        language="en",
                    ),
                    actor="editor",
                )
        except RuntimeError as exc:
            assert str(exc) == "audit failure"
        else:
            raise AssertionError(
                "update_knowledge() should have raised RuntimeError"
            )

        session.expire_all()

        persisted = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert persisted is not None
        assert persisted.state == "Active"
        assert persisted.statement_text == "Original knowledge statement"
        assert persisted.statement_language == "en"

        versions_after = (
            session.query(VersionModel)
            .filter(
                VersionModel.learning_object_id
                == learning_object.id
            )
            .order_by(VersionModel.number.asc())
            .all()
        )

        assert len(versions_after) == 1
        assert versions_after[0].number == 1
        assert (
            versions_after[0].snapshot["statement"]["text"]
            == "Original knowledge statement"
        )

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
            "LearningObjectApproved",
        ]

    finally:
        session.close()
        engine.dispose()


def test_retire_persists_retired_state_and_audit(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite://",
    )

    import importlib

    import app.persistence.database as database

    database = importlib.reload(database)

    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.audit_record_model import AuditRecordModel
    from app.persistence.models.base import Base
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

        with transaction(session):
            service.approve(
                learning_object.id,
                actor="reviewer",
            )

        session.expire_all()

        persisted = service.get(learning_object.id)

        assert persisted is not None
        assert persisted.state.value == "Active"

        with transaction(session):
            service.retire(
                learning_object.id,
                actor="reviewer",
            )

        session.expire_all()

        retired = service.get(learning_object.id)

        assert retired is not None
        assert retired.state.value == "Retired"

        versions = (
            session.query(VersionModel)
            .filter(
                VersionModel.learning_object_id
                == learning_object.id
            )
            .order_by(VersionModel.number.asc())
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
            .order_by(AuditRecordModel.timestamp.asc())
            .all()
        )

        assert [
            audit.event_type
            for audit in audits
        ] == [
            "LearningObjectCreated",
            "LearningObjectSubmitted",
            "LearningObjectApproved",
            "LearningObjectRetired",
        ]

    finally:
        session.close()
        engine.dispose()


def test_get_history_returns_persisted_versions_in_order(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite://",
    )

    import importlib

    import app.persistence.database as database

    database = importlib.reload(database)

    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.audit_record_model import AuditRecordModel
    from app.persistence.models.base import Base
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
                text="Original knowledge statement",
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
            service.approve(
                learning_object.id,
                actor="reviewer",
            )

        session.expire_all()

        with transaction(session):
            service.update_knowledge(
                learning_object.id,
                KnowledgeStatement(
                    text="Updated knowledge statement",
                    language="en",
                ),
                actor="editor",
            )

        session.expire_all()

        history = service.get_history(
            learning_object.id,
        )

        assert len(history) == 2

        assert history[0].number == 1
        assert (
            history[0].snapshot["statement"]["text"]
            == "Original knowledge statement"
        )
        assert (
            history[0].snapshot["statement"]["language"]
            == "en"
        )
        assert history[0].snapshot["state"] == "Active"

        assert history[1].number == 2
        assert (
            history[1].snapshot["statement"]["text"]
            == "Updated knowledge statement"
        )
        assert (
            history[1].snapshot["statement"]["language"]
            == "en"
        )
        assert history[1].snapshot["state"] == "Active"

    finally:
        session.close()
        engine.dispose()


def test_get_reconstructs_learning_object_with_examples_and_notes(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite://",
    )

    import importlib

    import app.persistence.database as database

    database = importlib.reload(database)

    from app.domain.entities.example import Example
    from app.domain.entities.knowledge_statement import KnowledgeStatement
    from app.domain.entities.note import Note
    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.base import Base
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

        service, repository = create_learning_object_service(
            session
        )

        learning_object = service.create_candidate(
            anchor_id=anchor_id,
            statement=KnowledgeStatement(
                text="Persisted knowledge statement",
                language="en",
            ),
            category_id=category_id,
            actor="creator",
        )

        session.flush()

        model = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert model is not None

        model.examples.add(
            LearningObjectExampleModel(
                learning_object_id=learning_object.id,
                content="Example one",
            )
        )

        model.examples.add(
            LearningObjectExampleModel(
                learning_object_id=learning_object.id,
                content="Example two",
            )
        )

        model.notes.add(
            LearningObjectNoteModel(
                learning_object_id=learning_object.id,
                content="Note one",
            )
        )

        model.notes.add(
            LearningObjectNoteModel(
                learning_object_id=learning_object.id,
                content="Note two",
            )
        )

        session.commit()
        session.expire_all()

        persisted = service.get(
            learning_object.id,
        )

        assert persisted.id == learning_object.id
        assert persisted.anchor_id == anchor_id
        assert persisted.category_id == category_id

        assert persisted.statement.text == (
            "Persisted knowledge statement"
        )
        assert persisted.statement.language == "en"

        assert persisted.state.value == "Candidate"

        assert persisted.examples == {
            Example(content="Example one"),
            Example(content="Example two"),
        }

        assert persisted.notes == {
            Note(content="Note one"),
            Note(content="Note two"),
        }

    finally:
        session.close()
        engine.dispose()


def test_invalid_retire_rolls_back_state_and_audit(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite://",
    )

    import importlib

    import app.persistence.database as database

    database = importlib.reload(database)

    from app.domain.entities.knowledge_statement import KnowledgeStatement
    from app.domain.entities.learning_object import (
        InvalidStateTransition,
        LearningObjectState,
    )
    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.audit_record_model import AuditRecordModel
    from app.persistence.models.base import Base
    from app.persistence.models.knowledge_category_model import (
        KnowledgeCategoryModel,
    )
    from app.persistence.models.learning_object_model import (
        LearningObjectModel,
    )
    from app.persistence.wiring import create_learning_object_service
    from app.persistence.transaction import transaction

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

        service, repository = create_learning_object_service(
            session
        )

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

        with pytest.raises(InvalidStateTransition):
            with transaction(session):
                service.retire(
                    learning_object.id,
                    actor="reviewer",
                )

        session.expire_all()

        persisted = repository.get_by_id(
            learning_object.id,
        )

        assert persisted is not None
        assert persisted.state == LearningObjectState.PROPOSED

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

        retired_audits = (
            session.query(AuditRecordModel)
            .filter(
                AuditRecordModel.entity_id
                == learning_object.id,
                AuditRecordModel.event_type
                == "LearningObjectRetired",
            )
            .all()
        )

        assert retired_audits == []

        model = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert model is not None
        assert model.state == "Proposed"

    finally:
        session.close()
        engine.dispose()
