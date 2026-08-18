from uuid import uuid4

from sqlalchemy import inspect

from app.domain.entities.knowledge_statement import KnowledgeStatement
from app.persistence.models.audit_record_model import AuditRecordModel
from app.persistence.models.learning_object_model import LearningObjectModel
from app.persistence.models.version_model import VersionModel
from app.persistence.transaction import transaction
from app.persistence.wiring import create_learning_object_service


def test_approve_persists_version_and_audit() -> None:
    from app.persistence.database import create_session

    session = create_session()

    try:
        service, _ = create_learning_object_service(session)

        learning_object = service.create_candidate(
            anchor_id=uuid4(),
            statement=KnowledgeStatement(
                text="Test knowledge statement",
                language="en",
            ),
            category_id=uuid4(),
            actor="test",
        )

        service.submit_for_review(
            learning_object.id,
            actor="producer",
        )

        with transaction(session):
            approved = service.approve(
                learning_object.id,
                actor="reviewer",
            )

        assert approved.state.value == "Active"

        session.expire_all()

        learning_object_model = session.get(
            LearningObjectModel,
            learning_object.id,
        )

        assert learning_object_model is not None
        assert learning_object_model.state == "Active"

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

    finally:
        session.close()
