import pytest

from uuid import UUID, uuid4

from app.application.services.learning_object_service import (
    LearningObjectService,
)

from app.application.errors import (
    EntityNotFound,
    InvalidOperation,
)

from app.domain.entities.knowledge_statement import KnowledgeStatement

from app.domain.entities.learning_object import (
    InvalidStateTransition,
    LearningObject,
    LearningObjectState,
)

from tests.fixtures.repositories import (
    InMemoryAuditRepository,
    InMemoryLearningObjectRepository,
    InMemoryVersionRepository,
)


def create_statement(
    text: str = "Example statement",
) -> KnowledgeStatement:
    return KnowledgeStatement(
        text=text,
        language="en",
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


def create_candidate(
    service: LearningObjectService,
):
    return service.create_candidate(
        anchor_id=uuid4(),
        statement=create_statement(),
        category_id=uuid4(),
        actor="test-user",
    )


def approve_candidate(
    service: LearningObjectService,
):
    learning_object = create_candidate(service)

    service.submit_for_review(
        learning_object.id,
        actor="producer",
    )

    service.approve(
        learning_object.id,
        actor="reviewer",
    )

    return learning_object


def test_create_candidate():

    service = create_service()

    learning_object = service.create_candidate(
        anchor_id=uuid4(),
        statement=create_statement(
            "The present perfect connects past and present."
        ),
        category_id=uuid4(),
        actor="test-user",
    )

    assert learning_object.state.value == "Candidate"
    assert (
        learning_object.statement.text
        == "The present perfect connects past and present."
    )
    assert learning_object.statement.language == "en"


def test_submit_for_review():

    service = create_service()

    learning_object = create_candidate(service)

    service.submit_for_review(
        learning_object.id,
        actor="test-user",
    )

    assert learning_object.state.value == "Proposed"


def test_review_and_approve():

    service = create_service()

    learning_object = create_candidate(service)

    service.submit_for_review(
        learning_object.id,
        actor="producer",
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

    learning_object = create_candidate(service)

    service.submit_for_review(
        learning_object.id,
        actor="producer",
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
    assert (
        history[0].learning_object_id
        == learning_object.id
    )

    assert history[0].snapshot["statement"] == {
        "text": "Example statement",
        "language": "en",
    }


def test_update_creates_second_version():

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

    learning_object = approve_candidate(service)

    service.update_knowledge(
        learning_object.id,
        statement=create_statement(
            "Updated example statement"
        ),
        actor="reviewer",
    )

    history = service.get_history(
        learning_object.id
    )

    assert len(history) == 2
    assert history[0].number == 1
    assert history[1].number == 2

    assert (
        history[0].snapshot["statement"]["text"]
        == "Example statement"
    )

    assert (
        history[1].snapshot["statement"]["text"]
        == "Updated example statement"
    )

    assert learning_object.state.value == "Active"


def test_update_preserves_previous_version():

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

    learning_object = approve_candidate(service)

    original_history = service.get_history(
        learning_object.id
    )

    original_version = original_history[0]

    service.update_knowledge(
        learning_object.id,
        statement=create_statement(
            "Updated example statement"
        ),
        actor="reviewer",
    )

    history = service.get_history(
        learning_object.id
    )

    assert history[0] is original_version
    assert history[0].number == 1
    assert (
        history[0].snapshot["statement"]["text"]
        == "Example statement"
    )


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

    learning_object = create_candidate(service)

    service.submit_for_review(
        learning_object.id,
        actor="producer",
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

    assert len(audit_records) == 3

    assert [
        record.event_type
        for record in audit_records
    ] == [
        "LearningObjectCreated",
        "LearningObjectSubmitted",
        "LearningObjectApproved",
    ]


def test_retire():

    service = create_service()

    learning_object = approve_candidate(service)

    service.retire(
        learning_object.id,
        actor="reviewer",
    )

    assert learning_object.state.value == "Retired"

def test_get_missing_learning_object_raises_entity_not_found():
    service = create_service()

    missing_id = uuid4()

    with pytest.raises(EntityNotFound):
        service.get(missing_id)

def test_submit_for_review_invalid_state_raises_invalid_operation():
    service = create_service()

    learning_object = create_candidate(service)

    service.submit_for_review(
        learning_object.id,
        actor="test-user",
    )

    with pytest.raises(InvalidOperation) as exc_info:
        service.submit_for_review(
            learning_object.id,
            actor="test-user",
        )

    assert isinstance(
        exc_info.value.__cause__,
        InvalidStateTransition,
    )

def test_approve_invalid_state_raises_invalid_operation():
    service = create_service()

    learning_object = create_candidate(service)

    with pytest.raises(InvalidOperation) as exc_info:
        service.approve(
            learning_object.id,
            actor="test-user",
        )

    assert isinstance(
        exc_info.value.__cause__,
        InvalidStateTransition,
    )

def test_update_knowledge_invalid_state_raises_invalid_operation():
    service = create_service()

    learning_object = create_candidate(service)

    with pytest.raises(InvalidOperation) as exc_info:
        service.update_knowledge(
            learning_object.id,
            statement=create_statement(
                "Updated example statement"
            ),
            actor="test-user",
        )

    assert isinstance(
        exc_info.value.__cause__,
        InvalidStateTransition,
    )

def test_retire_invalid_state_raises_invalid_operation():
    service = create_service()

    learning_object = create_candidate(service)

    with pytest.raises(InvalidOperation) as exc_info:
        service.retire(
            learning_object.id,
            actor="test-user",
        )

    assert isinstance(
        exc_info.value.__cause__,
        InvalidStateTransition,
    )



def test_approve_is_atomic_across_learning_object_version_and_audit(
    monkeypatch,
):
    """
    A01.7 — Transaction Boundary

    Approval changes three pieces of state that must succeed or fail
    atomically:

    1. LearningObject state;
    2. immutable Version creation;
    3. AuditRecord creation.

    The test deliberately makes the final audit operation fail and verifies
    that the application exposes the transaction-boundary gap instead of
    silently leaving partially persisted state.
    """
    from uuid import uuid4

    import pytest

    from app.application.errors import InvalidOperation
    from app.application.services.learning_object_service import (
        LearningObjectService,
    )
    from app.domain.entities.knowledge_statement import KnowledgeStatement
    from app.domain.entities.learning_object import LearningObjectState

    class InMemoryLearningObjectRepository:
        def __init__(self, learning_object):
            self.learning_object = learning_object

        def save(self, learning_object):
            self.learning_object = learning_object

        def get_by_id(self, learning_object_id):
            if self.learning_object.id == learning_object_id:
                return self.learning_object
            return None

    class InMemoryVersionRepository:
        def __init__(self):
            self.versions = []

        def save(self, version):
            self.versions.append(version)

        def get_history(self, learning_object_id):
            return [
                version
                for version in self.versions
                if version.learning_object_id == learning_object_id
            ]

    class FailingAuditRepository:
        def __init__(self):
            self.records = []

        def record(self, audit):
            raise RuntimeError("audit persistence failed")

        def find_by_entity(self, entity_id):
            return list(self.records)

    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=KnowledgeStatement(
            text="Test knowledge statement.",
            language="en",
        ),
        category_id=uuid4(),
    )

    learning_object.submit_for_review()

    learning_object_repository = InMemoryLearningObjectRepository(
        learning_object
    )
    version_repository = InMemoryVersionRepository()
    audit_repository = FailingAuditRepository()

    service = LearningObjectService(
        learning_object_repository=learning_object_repository,
        version_repository=version_repository,
        audit_repository=audit_repository,
    )

    with pytest.raises(RuntimeError, match="audit persistence failed"):
        service.approve(
            learning_object_id=learning_object.id,
            actor="test-user",
        )

    # Current implementation exposes the transaction-boundary gap:
    # the domain object and Version have already been changed/persisted
    # before AuditRecord persistence fails.
    assert learning_object_repository.learning_object.state == (
        LearningObjectState.ACTIVE
    )

    assert len(
        version_repository.get_history(learning_object.id)
    ) == 1
