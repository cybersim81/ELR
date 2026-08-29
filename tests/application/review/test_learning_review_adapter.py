from uuid import UUID

import pytest

from app.application.review.learning_review_adapter import (
    LearningReviewAdapter,
)
from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.entities.review_decision import ReviewDecision


class StubChangeProposalRepository:
    def __init__(self):
        self.items = []

    def add(self, proposal):
        self.items.append(proposal)


class StubReviewDecisionTraceRepository:
    def __init__(self):
        self.items = []

    def add(self, trace):
        self.items.append(trace)


class StubKnowledgeValidation:
    def __init__(self, valid=True, rationale="Knowledge valid."):
        self.valid = valid
        self.rationale = rationale

    def validate(self, proposal):
        return self.valid, self.rationale


class StubRepositoryConsistency:
    def __init__(self, consistent=True, rationale="Repository consistent."):
        self.consistent = consistent
        self.rationale = rationale

    def check(self, proposal):
        return self.consistent, self.rationale


class StubReviewDecisionService:
    def __init__(
        self,
        decision=ReviewDecision.APPROVE,
        rationale="Approved.",
    ):
        self.decision = decision
        self.rationale = rationale

    def decide(self, proposal):
        return self.decision, self.rationale


def make_adapter(
    knowledge_valid=True,
    knowledge_rationale="Knowledge valid.",
    repository_consistent=True,
    repository_rationale="Repository consistent.",
    decision=ReviewDecision.APPROVE,
    decision_rationale="Approved.",
):
    return LearningReviewAdapter(
        change_proposal_repository=(
            StubChangeProposalRepository()
        ),
        review_decision_trace_repository=(
            StubReviewDecisionTraceRepository()
        ),
        knowledge_validation=StubKnowledgeValidation(
            valid=knowledge_valid,
            rationale=knowledge_rationale,
        ),
        repository_consistency=StubRepositoryConsistency(
            consistent=repository_consistent,
            rationale=repository_rationale,
        ),
        review_decision_service=StubReviewDecisionService(
            decision=decision,
            rationale=decision_rationale,
        ),
    )


def make_proposal(
    change_type=ChangeType.CREATE,
    change_payload=None,
    change_evidence=None,
):
    return ChangeProposal(
        change_type=change_type,
        change_payload=(
            change_payload
            if change_payload is not None
            else {"statement": "Test statement"}
        ),
        proposal_rationale="Test proposal.",
        change_evidence=(
            change_evidence
            if change_evidence is not None
            else (
                {"type": "change", "source": "test"},
            )
        ),
    )


def test_review_approves_valid_proposal():
    adapter = make_adapter()

    proposal = make_proposal()
    reviewer = "test-reviewer"

    trace = adapter.review(
        proposal,
        reviewer,
    )

    assert trace.proposal_id == proposal.id
    assert trace.decision is ReviewDecision.APPROVE
    assert trace.reviewer == reviewer


def test_review_rejects_proposal_without_change_type():
    adapter = make_adapter()

    proposal = make_proposal(
        change_type=None,
    )

    trace = adapter.review(
        proposal,
        "test-reviewer",
    )

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Change Type is required."


def test_review_rejects_proposal_without_change_payload():
    adapter = make_adapter()

    proposal = make_proposal(
        change_payload={},
    )

    trace = adapter.review(
        proposal,
        "test-reviewer",
    )

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Change Payload is required."


def test_review_rejects_proposal_without_change_evidence():
    adapter = make_adapter()

    proposal = make_proposal(
        change_evidence=(),
    )

    trace = adapter.review(
        proposal,
        "test-reviewer",
    )

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Change Evidence is required."


def test_review_rejects_invalid_knowledge():
    adapter = make_adapter(
        knowledge_valid=False,
        knowledge_rationale="Knowledge validation failed.",
    )

    proposal = make_proposal()

    trace = adapter.review(
        proposal,
        "test-reviewer",
    )

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Knowledge validation failed."


def test_review_rejects_inconsistent_repository():
    adapter = make_adapter(
        repository_consistent=False,
        repository_rationale="Repository consistency failed.",
    )

    proposal = make_proposal()

    trace = adapter.review(
        proposal,
        "test-reviewer",
    )

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Repository consistency failed."


def test_review_persists_proposal_and_trace():
    proposal_repository = StubChangeProposalRepository()
    trace_repository = StubReviewDecisionTraceRepository()

    adapter = LearningReviewAdapter(
        change_proposal_repository=proposal_repository,
        review_decision_trace_repository=trace_repository,
        knowledge_validation=StubKnowledgeValidation(),
        repository_consistency=StubRepositoryConsistency(),
        review_decision_service=StubReviewDecisionService(),
    )

    proposal = make_proposal()

    trace = adapter.review(
        proposal,
        "test-reviewer",
    )

    assert proposal_repository.items == [proposal]
    assert trace_repository.items == [trace]


def test_review_returns_uuid_proposal_id():
    adapter = make_adapter()

    proposal = make_proposal()

    trace = adapter.review(
        proposal,
        "test-reviewer",
    )

    assert isinstance(trace.proposal_id, UUID)
