from uuid import uuid4

from app.application.services.learning_object_service import (
    LearningObjectService,
)
from app.domain.entities.audit_record import AuditRecord
from app.domain.entities.learning_object import (
    LearningObject,
)
from app.domain.entities.version import Version


class InMemoryLearningObjectRepository:

    def __init__(self):
        self.items = {}

    def save(self, learning_object):
        self.items[learning_object.id] = learning_object

    def get_by_id(self, object_id):
        return self.items.get(object_id)

    def delete(self, object_id):
        self.items.pop(object_id, None)


class InMemoryVersionRepository:

    def __init__(self):
        self.items = []

    def save(self, version):
        self.items.append(version)

    def get_history(self, entity_id):
        return [
            version
            for version in self.items
            if version.entity_id == entity_id
        ]


class InMemoryAuditRepository:

    def __init__(self):
        self.items = []

    def record(self, audit):
        self.items.append(audit)

    def find_by_entity(self, entity_id):
        return [
            audit
            for audit in self.items
            if audit.entity_id == entity_id
        ]


def create_service():

    return (
        LearningObjectService(
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

    history = service.get_history(
        learning_object.id
    )

    assert len(history) == 1
    assert history[0].number == 1
