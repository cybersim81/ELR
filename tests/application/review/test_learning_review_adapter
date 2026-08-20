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


def create_adapter():
    proposal_repository = InMemoryChangeProposalRepository()
    trace_repository = InMemoryReviewDecisionTraceRepository()

    adapter = LearningReviewAdapter(
        change_proposal_repository=proposal_repository,
        review_decision_trace_repository=trace_repository,
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
