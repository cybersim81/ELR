def test_e2e_07_production_persistence_flow(
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
                content="E2E-07 anchor",
                type="text",
                created_at=__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ),
            )
        )

        session.add(
            KnowledgeCategoryModel(
                id=category_id,
                name="E2E-07 category",
            )
        )

        session.commit()

        service, _ = create_learning_object_service(session)

        learning_object = service.create_candidate(
            anchor_id=anchor_id,
            statement=KnowledgeStatement(
                text="E2E-07 knowledge",
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
        assert persisted.anchor_id == anchor_id
        assert persisted.category_id == category_id
        assert persisted.statement_text == "E2E-07 knowledge"
        assert persisted.statement_language == "en"
        assert persisted.state == "Active"

        versions = (
            session.query(VersionModel)
            .filter(
                VersionModel.learning_object_id
                == learning_object.id,
            )
            .order_by(VersionModel.number.asc())
            .all()
        )

        assert len(versions) == 1
        assert versions[0].number == 1
        assert versions[0].snapshot["statement"]["text"] == (
            "E2E-07 knowledge"
        )
        assert versions[0].snapshot["state"] == "Active"

        audits = (
            session.query(AuditRecordModel)
            .filter(
                AuditRecordModel.entity_id
                == learning_object.id,
            )
            .order_by(
                AuditRecordModel.timestamp.asc()
            )
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

        assert audits[-1].actor == "reviewer"
        assert audits[-1].metadata_ == {"version": 1}

    finally:
        session.close()
        engine.dispose()
