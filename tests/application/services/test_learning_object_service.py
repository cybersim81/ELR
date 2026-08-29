from uuid import uuid4

import pytest

from app.application.errors import EntityNotFound
from app.application.security.identity import IdentityContext
from app.application.security.roles import Role
from app.application.services.learning_object_service import (
    LearningObjectService,
)
from app.domain.entities.knowledge_statement import (
    KnowledgeStatement,
)
from app.domain.entities.learning_object import (
    LearningObject,
)


class StubLearningObjectRepository:
    def __init__(self):
        self.items = {}

    def save(self, learning_object):
        self.items[learning_object.id] = learning_object

    def get_by_id(self, learning_object_id):
        return self.items.get(learning_object_id)


class StubVersionRepository:
    def __init__(self):
        self.items = []

    def get_history(self, learning_object_id):
        return [
            item
            for item in self.items
            if item.learning_object_id == learning_object_id
        ]


class StubAuditRepository:
    def __init__(self):
        self.items = []

    def record(self, audit_record):
        self.items.append(audit_record)


class StubEventRecordRepository:
    def __init__(self):
        self.items = []

    def save(self, event_record):
        self.items.append(event_record)


class StubTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def make_identity(
    role=Role.KNOWLEDGE_PRODUCER,
):
    return IdentityContext(
        actor_id=uuid4(),
        actor_type="Human",
        roles=frozenset({role.value}),
    )


def make_service():
    learning_object_repository = (
        StubLearningObjectRepository()
    )
    version_repository = StubVersionRepository()
    audit_repository = StubAuditRepository()
    event_record_repository = (
        StubEventRecordRepository()
    )

    service = LearningObjectService(
        learning_object_repository=learning_object_repository,
        version_repository=version_repository,
        audit_repository=audit_repository,
        event_record_repository=event_record_repository,
    )

    return (
        service,
        learning_object_repository,
        version_repository,
        audit_repository,
        event_record_repository,
    )


def make_statement():
    return KnowledgeStatement(
        text="Test knowledge statement.",
    )


def test_create_candidate_creates_learning_object():
    (
        service,
        learning_object_repository,
        _,
        _,
        _,
    ) = make_service()

    actor = make_identity()

    learning_object = service.create_candidate(
        anchor_id=uuid4(),
        statement=make_statement(),
        category_id=uuid4(),
        actor=actor,
    )

    assert isinstance(
        learning_object,
        LearningObject,
    )
    assert (
        learning_object_repository.get_by_id(
            learning_object.id
        )
        is learning_object
    )


def test_create_candidate_records_actor_identity():
    (
        service,
        _,
        _,
        audit_repository,
        _,
    ) = make_service()

    actor = make_identity()

    learning_object = service.create_candidate(
        anchor_id=uuid4(),
        statement=make_statement(),
        category_id=uuid4(),
        actor=actor,
    )

    assert len(audit_repository.items) == 1
    assert (
        audit_repository.items[0].actor
        == str(actor.actor_id)
    )
    assert (
        audit_repository.items[0].entity_id
        == learning_object.id
    )


def test_create_candidate_rejects_unauthorized_actor():
    (
        service,
        learning_object_repository,
        _,
        audit_repository,
        _,
    ) = make_service()

    actor = make_identity(
        role=Role.KNOWLEDGE_REVIEWER,
    )

    with pytest.raises(Exception):
        service.create_candidate(
            anchor_id=uuid4(),
            statement=make_statement(),
            category_id=uuid4(),
            actor=actor,
        )

    assert learning_object_repository.items == {}
    assert audit_repository.items == []


def test_get_returns_learning_object():
    (
        service,
        learning_object_repository,
        _,
        _,
        _,
    ) = make_service()

    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=make_statement(),
        category_id=uuid4(),
    )

    learning_object_repository.save(
        learning_object
    )

    result = service.get(
        learning_object.id
    )

    assert result is learning_object


def test_get_raises_entity_not_found():
    (
        service,
        _,
        _,
        _,
        _,
    ) = make_service()

    with pytest.raises(EntityNotFound):
        service.get(uuid4())


def test_get_history_returns_version_history():
    (
        service,
        learning_object_repository,
        version_repository,
        _,
        _,
    ) = make_service()

    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=make_statement(),
        category_id=uuid4(),
    )

    learning_object_repository.save(
        learning_object
    )

    result = service.get_history(
        learning_object.id
    )

    assert result == []


def test_submit_for_review_uses_actor():
    (
        service,
        learning_object_repository,
        _,
        audit_repository,
        _,
    ) = make_service()

    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=make_statement(),
        category_id=uuid4(),
    )

    learning_object_repository.save(
        learning_object
    )

    result = service.submit_for_review(
        learning_object.id,
        "test-user",
    )

    assert result is learning_object
    assert len(audit_repository.items) == 1
    assert (
        audit_repository.items[0].actor
        == "test-user"
    )


def test_approve_creates_learning_object_version():
    (
        service,
        learning_object_repository,
        _,
        audit_repository,
        _,
    ) = make_service()

    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=make_statement(),
        category_id=uuid4(),
    )

    learning_object_repository.save(
        learning_object
    )

    learning_object.submit_for_review()

    result = service.approve(
        learning_object.id,
        "test-reviewer",
    )

    assert result is learning_object
    assert len(audit_repository.items) == 1
    assert (
        audit_repository.items[0].actor
        == "test-reviewer"
    )


def test_update_knowledge_keeps_learning_object_active():
    (
        service,
        learning_object_repository,
        _,
        audit_repository,
        event_record_repository,
    ) = make_service()

    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=make_statement(),
        category_id=uuid4(),
    )

    learning_object_repository.save(
        learning_object
    )

    learning_object.submit_for_review()
    learning_object.approve()

    result = service.update_knowledge(
        learning_object.id,
        KnowledgeStatement(
            text="Updated knowledge statement.",
        ),
        "test-user",
    )

    assert result is learning_object
    assert len(audit_repository.items) == 1
    assert len(event_record_repository.items) == 1


def test_retire_changes_learning_object_state():
    (
        service,
        learning_object_repository,
        _,
        audit_repository,
        _,
    ) = make_service()

    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=make_statement(),
        category_id=uuid4(),
    )

    learning_object_repository.save(
        learning_object
    )

    learning_object.submit_for_review()
    learning_object.approve()

    result = service.retire(
        learning_object.id,
        "test-user",
    )

    assert result is learning_object
    assert len(audit_repository.items) == 1
    assert (
        audit_repository.items[0].actor
        == "test-user"
    )
