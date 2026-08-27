```python
from uuid import uuid4

import pytest

from app.application.errors import InvalidOperation
from app.application.services.audit_service import AuditService
from app.application.services.learning_object_change_applier import (
    LearningObjectChangeApplier,
)
from app.application.services.version_service import VersionService
from app.domain.entities.audit_record import AuditRecord
from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.entities.knowledge_statement import KnowledgeStatement
from app.domain.entities.learning_object import (
    LearningObject,
    LearningObjectState,
)
from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.entities.version import Version
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.learning_object_repository import (
    LearningObjectRepository,
)
from app.domain.repositories.version_repository import VersionRepository


class InMemoryLearningObjectRepository(
    LearningObjectRepository
):
    def __init__(self) -> None:
        self.items: dict = {}

    def save(self, learning_object: LearningObject) -> None:
        self.items[learning_object.id] = learning_object

    def get_by_id(self, object_id):
        return self.items.get(object_id)


class InMemoryVersionRepository(VersionRepository):
    def __init__(self) -> None:
        self.items: dict = {}

    def save(self, version: Version) -> None:
        self.items.setdefault(
            version.learning_object_id,
            [],
        ).append(version)

    def get_history(self, learning_object_id):
        return self.items.get(
            learning_object_id,
            [],
        )


class InMemoryAuditRepository(AuditRepository):
    def __init__(self) -> None:
        self.items: list[AuditRecord] = []

    def record(self, audit: AuditRecord) -> None:
        self.items.append(audit)

    def find_by_entity(
        self,
        entity_id,
    ) -> list[AuditRecord]:
        return [
            audit
            for audit in self.items
            if audit.entity_id == entity_id
        ]


def make_applier():
    learning_object_repository = (
        InMemoryLearningObjectRepository()
    )
    version_repository = InMemoryVersionRepository()
    audit_repository = InMemoryAuditRepository()

    applier = LearningObjectChangeApplier(
        learning_object_repository=(
            learning_object_repository
        ),
        version_service=VersionService(
            version_repository
        ),
        audit_service=AuditService(
            audit_repository
        ),
    )

    return (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    )


def make_approved_trace(
    proposal: ChangeProposal,
) -> ReviewDecisionTrace:
    return ReviewDecisionTrace(
        proposal_id=proposal.id,
        decision=ReviewDecision.APPROVE,
    )


def make_active_learning_object() -> LearningObject:
    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=KnowledgeStatement(
            text="Existing statement",
            language="en",
        ),
        category_id=uuid4(),
    )

    learning_object.submit_for_review()
    learning_object.approve()

    return learning_object


def make_update_proposal(
    learning_object: LearningObject,
    change_type: ChangeType,
    text: str,
) -> ChangeProposal:
    return ChangeProposal(
        change_type=change_type,
        change_payload={
            "learning_object_id": str(
                learning_object.id
            ),
            "statement": {
                "text": text,
                "language": "en",
            },
        },
        proposal_rationale=(
            "Update the representation of the "
            "existing linguistic knowledge."
        ),
        change_evidence=(
            {
                "type": "example",
                "content": text,
            },
        ),
    )


def test_apply_create_creates_learning_object():
    (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    ) = make_applier()

    anchor_id = uuid4()
    category_id = uuid4()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "anchor_id": str(anchor_id),
            "category_id": str(category_id),
            "statement": {
                "text": (
                    '"Weever" is the English term '
                    'for "tracina".'
                ),
                "language": "en",
            },
        },
        proposal_rationale=(
            "The knowledge is not represented "
            "in the repository."
        ),
        change_evidence=(
            {
                "type": "example",
                "content": (
                    '"Weever" is the English term '
                    'for "tracina".'
                ),
            },
        ),
    )

    trace = make_approved_trace(proposal)

    result = applier.apply(
        proposal=proposal,
        review_trace=trace,
        actor="test",
    )

    assert result.anchor_id == anchor_id
    assert result.category_id == category_id
    assert (
        result.statement.text
        == '"Weever" is the English term for "tracina".'
    )

    assert (
        learning_object_repository.get_by_id(
            result.id
        )
        is result
    )

    history = version_repository.get_history(
        result.id
    )

    assert len(history) == 1
    assert history[0].number == 1

    assert len(audit_repository.items) == 1
    assert audit_repository.items[0].entity_id == result.id
    assert (
        audit_repository.items[0].event_type
        == "LearningObjectCreated"
    )


def test_apply_update_evolves_existing_identity():
    (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    ) = make_applier()

    learning_object = make_active_learning_object()

    learning_object_repository.save(
        learning_object
    )

    initial_version = VersionService(
        version_repository
    ).create_version(
        learning_object
    )

    proposal = make_update_proposal(
        learning_object=learning_object,
        change_type=ChangeType.UPDATE,
        text=(
            "Since introduces the starting point "
            "of a duration."
        ),
    )

    trace = make_approved_trace(proposal)

    result = applier.apply(
        proposal=proposal,
        review_trace=trace,
        actor="test",
    )

    assert result.id == learning_object.id
    assert result is learning_object
    assert result.state is LearningObjectState.ACTIVE
    assert (
        result.statement.text
        == (
            "Since introduces the starting point "
            "of a duration."
        )
    )

    history = version_repository.get_history(
        result.id
    )

    assert len(history) == 2
    assert history[0].number == initial_version.number
    assert history[1].number == 2
    assert (
        history[1].snapshot["statement"]["text"]
        == (
            "Since introduces the starting point "
            "of a duration."
        )
    )

    assert len(audit_repository.items) == 1
    assert (
        audit_repository.items[0].event_type
        == "LearningObjectUpdated"
    )


def test_apply_merge_evolves_existing_identity():
    (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    ) = make_applier()

    learning_object = make_active_learning_object()

    learning_object_repository.save(
        learning_object
    )

    VersionService(
        version_repository
    ).create_version(
        learning_object
    )

    proposal = make_update_proposal(
        learning_object=learning_object,
        change_type=ChangeType.MERGE,
        text=(
            "Take can also be used with picture "
            "to indicate taking a photograph."
        ),
    )

    trace = make_approved_trace(proposal)

    result = applier.apply(
        proposal=proposal,
        review_trace=trace,
        actor="test",
    )

    assert result.id == learning_object.id
    assert result is learning_object
    assert result.state is LearningObjectState.ACTIVE
    assert (
        result.statement.text
        == (
            "Take can also be used with picture "
            "to indicate taking a photograph."
        )
    )

    history = version_repository.get_history(
        result.id
    )

    assert len(history) == 2
    assert history[0].number == 1
    assert history[1].number == 2
    assert (
        history[1].snapshot["statement"]["text"]
        == (
            "Take can also be used with picture "
            "to indicate taking a photograph."
        )
    )

    assert len(audit_repository.items) == 1
    assert (
        audit_repository.items[0].event_type
        == "LearningObjectMerged"
    )


def test_apply_rejects_non_approved_proposal():
    (
        applier,
        _,
        _,
        _,
    ) = make_applier()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "anchor_id": str(uuid4()),
            "category_id": str(uuid4()),
            "statement": {
                "text": "Test statement",
                "language": "en",
            },
        },
        proposal_rationale="Test rationale",
    )

    trace = ReviewDecisionTrace(
        proposal_id=proposal.id,
        decision=ReviewDecision.REJECT,
    )

    with pytest.raises(
        InvalidOperation,
        match="Only approved Change Proposals",
    ):
        applier.apply(
            proposal=proposal,
            review_trace=trace,
            actor="test",
        )


def test_apply_rejects_trace_for_different_proposal():
    (
        applier,
        _,
        _,
        _,
    ) = make_applier()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "anchor_id": str(uuid4()),
            "category_id": str(uuid4()),
            "statement": {
                "text": "Test statement",
                "language": "en",
            },
        },
        proposal_rationale="Test rationale",
    )

    other_proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "anchor_id": str(uuid4()),
            "category_id": str(uuid4()),
            "statement": {
                "text": "Other statement",
                "language": "en",
            },
        },
        proposal_rationale="Other rationale",
    )

    trace = make_approved_trace(other_proposal)

    with pytest.raises(
        InvalidOperation,
        match="does not belong",
    ):
        applier.apply(
            proposal=proposal,
            review_trace=trace,
            actor="test",
        )


def test_apply_update_rejects_missing_target():
    (
        applier,
        _,
        _,
        _,
    ) = make_applier()

    proposal = ChangeProposal(
        change_type=ChangeType.UPDATE,
        change_payload={
            "learning_object_id": str(uuid4()),
            "statement": {
                "text": "Updated statement",
                "language": "en",
            },
        },
        proposal_rationale="Test rationale",
    )

    trace = make_approved_trace(proposal)

    with pytest.raises(
        InvalidOperation,
        match="was not found",
    ):
        applier.apply(
            proposal=proposal,
            review_trace=trace,
            actor="test",
        )


def test_apply_merge_rejects_invalid_target_id():
    (
        applier,
        _,
        _,
        _,
    ) = make_applier()

    proposal = ChangeProposal(
        change_type=ChangeType.MERGE,
        change_payload={
            "learning_object_id": "not-a-uuid",
            "statement": {
                "text": "Merged statement",
                "language": "en",
            },
        },
        proposal_rationale="Test rationale",
    )

    trace = make_approved_trace(proposal)

    with pytest.raises(
        InvalidOperation,
        match="target Learning Object id is invalid",
    ):
        applier.apply(
            proposal=proposal,
            review_trace=trace,
            actor="test",
        )


def test_apply_update_rejects_invalid_statement():
    (
        applier,
        learning_object_repository,
        _,
        _,
    ) = make_applier()

    learning_object = make_active_learning_object()

    learning_object_repository.save(
        learning_object
    )

    proposal = ChangeProposal(
        change_type=ChangeType.UPDATE,
        change_payload={
            "learning_object_id": str(
                learning_object.id
            ),
            "statement": {
                "text": "Updated statement",
            },
        },
        proposal_rationale="Test rationale",
    )

    trace = make_approved_trace(proposal)

    with pytest.raises(
        InvalidOperation,
        match="invalid Knowledge Statement",
    ):
        applier.apply(
            proposal=proposal,
            review_trace=trace,
            actor="test",
        )
