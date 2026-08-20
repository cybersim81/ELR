from uuid import uuid4

import pytest

from app.application.review.learning_review_adapter import (
    LearningReviewAdapter,
)
from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.entities.review_decision import ReviewDecision


class InMemoryChangeProposalRepository:
    def __init__(self):
        self.items = {}

    def add(self, proposal):
        self.items[proposal.id] = proposal

    def get_by_id(self, proposal_id):
        return self.items.get(proposal_id)


class InMemoryReviewDecisionTraceRepository:
    def __init__(self):
        self.items = []

    def add(self, trace):
        self.items.append(trace)

    def get_by_id(self, trace_id):
        return next(
            (
                trace
                for trace in self.items
                if trace.id == trace_id
            ),
            None,
        )

    def get_by_proposal_id(self, proposal_id):
        return [
            trace
            for trace in self.items
            if trace.proposal_id == proposal_id
        ]

class InMemoryKnowledgeValidation:
    def __init__(
        self,
        valid=True,
        rationale="Knowledge validation passed.",
    ):
        self.valid = valid
        self.rationale = rationale
        self.proposals = []

    def validate(self, proposal):
        self.proposals.append(proposal)
        return self.valid, self.rationale

def create_adapter(
    knowledge_validation=None,
):
    proposal_repository = InMemoryChangeProposalRepository()
    trace_repository = InMemoryReviewDecisionTraceRepository()

    if knowledge_validation is None:
        knowledge_validation = InMemoryKnowledgeValidation()

    adapter = LearningReviewAdapter(
        change_proposal_repository=proposal_repository,
        review_decision_trace_repository=trace_repository,
        knowledge_validation=knowledge_validation,
    )

    return (
        adapter,
        proposal_repository,
        trace_repository,
    )


def create_valid_proposal():
    return ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "anchor": "weever",
            "statement": "weever → tracina",
        },
        proposal_rationale="Candidate linguistic knowledge.",
        change_evidence=("evidence-1",),
    )


def test_review_rejects_proposal_without_change_type():
    adapter, _, traces = create_adapter()

    proposal = ChangeProposal(
        change_type=None,
        change_payload={"statement": "Test statement"},
        proposal_rationale="Test rationale.",
        change_evidence=("evidence-1",),
    )

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Change Type is required."
    assert traces.get_by_id(trace.id) is trace


def test_review_rejects_proposal_without_change_payload():
    adapter, _, traces = create_adapter()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={},
        proposal_rationale="Test rationale.",
        change_evidence=("evidence-1",),
    )

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Change Payload is required."
    assert traces.get_by_id(trace.id) is trace


def test_review_rejects_proposal_without_change_evidence():
    adapter, _, traces = create_adapter()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "statement": "Test statement",
        },
        proposal_rationale="Test rationale.",
        change_evidence=(),
    )

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Change Evidence is required."
    assert traces.get_by_id(trace.id) is trace


def test_review_persists_proposal_before_evaluation():
    adapter, proposals, _ = create_adapter()

    proposal = create_valid_proposal()

    with pytest.raises(
        NotImplementedError,
        match="Knowledge Validation",
    ):
        adapter.review(proposal)

    assert proposals.get_by_id(proposal.id) is proposal

def test_review_rejects_proposal_when_knowledge_validation_fails():
    knowledge_validation = InMemoryKnowledgeValidation(
        valid=False,
        rationale="Knowledge conflict detected.",
    )

    adapter, proposal_repository, trace_repository = (
        create_adapter(knowledge_validation)
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Knowledge conflict detected."

    assert knowledge_validation.proposals == [proposal]
    assert proposal_repository.get_by_id(proposal.id) is proposal
    assert trace_repository.get_by_id(trace.id) is trace

def test_review_proceeds_after_successful_knowledge_validation():
    knowledge_validation = InMemoryKnowledgeValidation(
        valid=True,
        rationale="Knowledge validation passed.",
    )

    adapter, proposal_repository, _ = create_adapter(
        knowledge_validation
    )

    proposal = create_valid_proposal()

    with pytest.raises(
        NotImplementedError,
        match="Repository Consistency Check",
    ):
        adapter.review(proposal)

    assert knowledge_validation.proposals == [proposal]
    assert proposal_repository.get_by_id(proposal.id) is proposal
