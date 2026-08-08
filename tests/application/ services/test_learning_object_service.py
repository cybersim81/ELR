```python
from uuid import uuid4

from app.application.services.learning_object_service import (
    LearningObjectService,
)
from tests.fixtures.repositories import (
    InMemoryAuditRepository,
    InMemoryLearningObjectRepository,
    InMemoryVersionRepository,
)


def create_service():

    return LearningObjectService(
        learning_object_repository=(
            InMemoryLearningObjectRepository()
        ),
        version_repository=(
            InMemoryVersionRepository()
        ),
        audit_repository=(
            InMemoryAuditRepository()
        ),
    )


def test_create_candidate():

    service = create_service()

    learning_object = service.create_candidate(
        anchor_id=uuid4(),
        statement="The present perfect connects past and present.",
        category_id=uuid4(),
        actor="test-user",
    )

    assert learning_object.state.value == "Candidate"


def test_submit_for_review():

    service = create_service()

    learning_object = service.create_candidate(
        anchor_id=uuid4(),
        statement="Example statement",
        category_id=uuid4(),
        actor="test-user",
    )

    service.submit_for_review(
        learning_object.id,
        actor="test-user",
    )

    assert learning_object.state.value == "Proposed"


def test_mark_reviewed():

    service = create_service()

    learning_object = service.create_candidate(
        anchor_id=uuid4(),
        statement="Example statement",
        category_id=uuid4(),
        actor="producer",
    )

    service.submit_for_review(
        learning_object.id,
        actor="producer",
    )

    service.mark_reviewed(
        learning_object.id,
        actor="reviewer",
    )

    assert learning_object.state.value == "Reviewed"


def test_review_and_approve():

    service = create_service()

    learning_object = service.create_candidate(
        anchor_id=uuid4(),
        statement="Example statement",
        category_id=uuid4(),
        actor="producer",
    )

    service.submit_for_review(
        learning_object.id,
        actor="producer",
    )

    service.mark_reviewed(
        learning_object.id,
        actor="reviewer",
    )

    service.approve(
        learning_object.id,
        actor="reviewer",
    )

    assert learning_object.state.value == "Active"


def test_approval_creates_version():

    version_repository = InMemoryVersionRepository()

    service = LearningObjectService(
        learning_object_repository=(
            InMemoryLearningObjectRepository()
        ),
        version_repository=version_repository,
        audit_repository=(
            InMemoryAuditRepository()
        ),
    )

    learning_object = service.create_candidate(
        anchor_id=uuid4(),
        statement="Example statement",
        category_id=uuid4(),
        actor="producer",
    )

    service.submit_for_review(
        learning_object.id,
        actor="producer",
    )

    service.mark_reviewed(
        learning_object.id,
        actor="reviewer",
    )

    service.approve(
        learning_object.id,
        actor="reviewer",
    )

    history = service.get_history(
        learning_object.id
    )

    assert len(history) == 1
    assert history[0].number == 1


def test_operations_create_audit_records():

    audit_repository = InMemoryAuditRepository()

    service = LearningObjectService(
        learning_object_repository=(
            InMemoryLearningObjectRepository()
        ),
        version_repository=(
            InMemoryVersionRepository()
        ),
        audit_repository=audit_repository,
    )

    learning_object = service.create_candidate(
        anchor_id=uuid4(),
        statement="Example statement",
        category_id=uuid4(),
        actor="producer",
    )

    service.submit_for_review(
        learning_object.id,
        actor="producer",
    )

    service.mark_reviewed(
        learning_object.id,
        actor="reviewer",
    )

    service.approve(
        learning_object.id,
        actor="reviewer",
    )

    audit_records = (
        audit_repository.find_by_entity(
            learning_object.id
        )
    )

    assert len(audit_records) == 4

    assert [
        record.event_type
        for record in audit_records
    ] == [
        "LearningObjectCreated",
        "LearningObjectSubmitted",
        "LearningObjectReviewed",
        "LearningObjectApproved",
    ]
```
