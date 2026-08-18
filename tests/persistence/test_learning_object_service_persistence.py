from uuid import uuid4

from app.application.services.learning_object_service import (
    LearningObjectService,
)
from app.domain.entities.knowledge_statement import KnowledgeStatement
from app.persistence.repositories.audit_repository import (
    SQLAlchemyAuditRepository,
)
from app.persistence.repositories.learning_object_repository import (
    SQLAlchemyLearningObjectRepository,
)
from app.persistence.repositories.version_repository import (
    SQLAlchemyVersionRepository,
)


def test_approve_coordinates_all_sqlalchemy_repositories() -> None:
    from sqlalchemy.orm import Session

    session = Session()

    learning_object_repository = SQLAlchemyLearningObjectRepository(
        session
    )
    version_repository = SQLAlchemyVersionRepository(session)
    audit_repository = SQLAlchemyAuditRepository(session)

    service = LearningObjectService(
        learning_object_repository=learning_object_repository,
        version_repository=version_repository,
        audit_repository=audit_repository,
    )

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

    approved = service.approve(
        learning_object.id,
        actor="reviewer",
    )

    assert approved.state.value == "Active"

    assert learning_object_repository._session is session
    assert version_repository._session is session
    assert audit_repository._session is session

    models = list(session.new)

    learning_object_models = [
        model
        for model in models
        if model.__class__.__name__ == "LearningObjectModel"
    ]

    version_models = [
        model
        for model in models
        if model.__class__.__name__ == "VersionModel"
    ]

    audit_models = [
        model
        for model in models
        if model.__class__.__name__ == "AuditRecordModel"
    ]

    assert len(learning_object_models) == 1
    assert len(version_models) == 1
    assert len(audit_models) == 3

    assert learning_object_models[0].id == learning_object.id
    assert learning_object_models[0].state == "Active"

    assert version_models[0].learning_object_id == learning_object.id
    assert version_models[0].number == 1

    assert [
        model.event_type
        for model in audit_models
    ] == [
        "LearningObjectCreated",
        "LearningObjectSubmitted",
        "LearningObjectApproved",
    ]

    assert audit_models[-1].actor == "reviewer"

    session.close()
