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
from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)


class InMemoryLearningObjectRepository:
    def __init__(self):
        self.items = {}

    def save(self, learning_object):
        self.items[learning_object.id] = learning_object

    def get_by_id(self, object_id):
        return self.items.get(object_id)


class InMemoryVersionRepository:
    def __init__(self):
        self.items = []

    def save(self, version):
        self.items.append(version)

    def get_history(self, learning_object_id):
        return [
            version
            for version in self.items
            if version.learning_object_id == learning_object_id
        ]


class InMemoryAuditRepository:
    def __init__(self):
        self.items = []

    def record(self, audit_record):
        self.items.append(audit_record)


def create_applier():
    learning_object_repository = (
        InMemoryLearningObjectRepository()
    )
    version_repository = InMemoryVersionRepository()
    audit_repository = InMemoryAuditRepository()

    version_service = VersionService(
        version_repository
    )

    audit_service = AuditService(
        audit_repository
    )

    applier = LearningObjectChangeApplier(
        learning_object_repository=learning_object_repository,
        version_service=version_service,
        audit_service=audit_service,
    )

    return (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    )


def create_proposal():
    return ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "anchor_id": str(uuid4()),
            "category_id": str(uuid4()),
            "statement": {
                "text": "The present perfect connects past and present.",
                "language": "en",
            },
        },
        proposal_rationale="Create a new atomic Learning Object.",
        change_evidence=(
            {
                "source": "test-evidence",
            },
        ),
    )


def create_trace(proposal, decision=ReviewDecision.APPROVE):
    return ReviewDecisionTrace(
        proposal_id=proposal.id,
        decision=decision,
        rationale="Review decision.",
        reviewer="test-reviewer",
    )


def test_apply_create_requires_approval():
    (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    ) = create_applier()

    proposal = create_proposal()

    trace = create_trace(
        proposal,
        decision=ReviewDecision.REJECT,
    )

    with pytest.raises(
        InvalidOperation,
        match="Only approved Change Proposals",
    ):
        applier.apply(
            proposal=proposal,
            review_trace=trace,
            actor="test-user",
        )

    assert learning_object_repository.items == {}
    assert version_repository.items == []
    assert audit_repository.items == []


def test_apply_create_requires_matching_review_trace():
    (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    ) = create_applier()

    proposal = create_proposal()

    unrelated_proposal = create_proposal()

    trace = create_trace(
        unrelated_proposal,
        decision=ReviewDecision.APPROVE,
    )

    with pytest.raises(
        InvalidOperation,
        match="does not belong",
    ):
        applier.apply(
            proposal=proposal,
            review_trace=trace,
            actor="test-user",
        )

    assert learning_object_repository.items == {}
    assert version_repository.items == []
    assert audit_repository.items == []


def test_apply_create_persists_learning_object_and_first_version():
    (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    ) = create_applier()

    proposal = create_proposal()
    trace = create_trace(proposal)

    learning_object = applier.apply(
        proposal=proposal,
        review_trace=trace,
        actor="test-user",
    )

    assert (
        learning_object_repository.get_by_id(
            learning_object.id
        )
        is learning_object
    )

    assert str(learning_object.anchor_id) == (
        proposal.change_payload["anchor_id"]
    )

    assert (
        learning_object.statement.text
        == proposal.change_payload["statement"]["text"]
    )

    assert (
        learning_object.statement.language
        == proposal.change_payload["statement"]["language"]
    )

    assert len(version_repository.items) == 1

    version = version_repository.items[0]

    assert version.learning_object_id == learning_object.id
    assert version.number == 1

    assert len(audit_repository.items) == 1

    audit = audit_repository.items[0]

    assert audit.entity_id == learning_object.id
    assert audit.event_type == "LearningObjectCreated"
    assert audit.actor == "test-user"
    assert audit.metadata["version"] == 1
    assert audit.metadata["proposal_id"] == str(proposal.id)
    assert audit.metadata["review_trace_id"] == str(trace.id)


def test_apply_create_rejects_invalid_payload():
    (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    ) = create_applier()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "anchor_id": "not-a-uuid",
            "category_id": str(uuid4()),
            "statement": {
                "text": "Test statement.",
                "language": "en",
            },
        },
        proposal_rationale="Invalid CREATE payload.",
        change_evidence=(
            {
                "source": "test-evidence",
            },
        ),
    )

    trace = create_trace(proposal)

    with pytest.raises(
        InvalidOperation,
        match="invalid.*payload",
    ):
        applier.apply(
            proposal=proposal,
            review_trace=trace,
            actor="test-user",
        )

    assert learning_object_repository.items == {}
    assert version_repository.items == []
    assert audit_repository.items == []


def test_apply_create_rejects_unsupported_change_type():
    (
        applier,
        learning_object_repository,
        version_repository,
        audit_repository,
    ) = create_applier()

    proposal = ChangeProposal(
        change_type=ChangeType.UPDATE,
        change_payload={
            "anchor_id": str(uuid4()),
            "category_id": str(uuid4()),
            "statement": {
                "text": "Test statement.",
                "language": "en",
            },
        },
        proposal_rationale="Unsupported change type.",
        change_evidence=(
            {
                "source": "test-evidence",
            },
        ),
    )

    trace = create_trace(proposal)

    with pytest.raises(
        InvalidOperation,
        match="Only CREATE",
    ):
        applier.apply(
            proposal=proposal,
            review_trace=trace,
            actor="test-user",
        )

    assert learning_object_repository.items == {}
    assert version_repository.items == []
    assert audit_repository.items == []
