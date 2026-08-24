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

class InMemoryRepositoryConsistency:
    def __init__(
        self,
        consistent=True,
        rationale="Repository consistency check passed.",
    ):
        self.consistent = consistent
        self.rationale = rationale
        self.proposals = []

    def check(self, proposal):
        self.proposals.append(proposal)
        return self.consistent, self.rationale

class InMemoryReviewDecisionService:
    def __init__(
        self,
        decision=ReviewDecision.APPROVE,
        rationale="Review approved.",
    ):
        self.decision = decision
        self.rationale = rationale
        self.proposals = []

    def decide(self, proposal):
        self.proposals.append(proposal)
        return self.decision, self.rationale

def create_adapter(
    knowledge_validation=None,
    repository_consistency=None,
    review_decision_service=None,
):
    proposal_repository = InMemoryChangeProposalRepository()
    trace_repository = InMemoryReviewDecisionTraceRepository()

    if knowledge_validation is None:
        knowledge_validation = InMemoryKnowledgeValidation()

    if repository_consistency is None:
        repository_consistency = InMemoryRepositoryConsistency()

    if review_decision_service is None:
        review_decision_service = InMemoryReviewDecisionService()

    adapter = LearningReviewAdapter(
        change_proposal_repository=proposal_repository,
        review_decision_trace_repository=trace_repository,
        knowledge_validation=knowledge_validation,
        repository_consistency=repository_consistency,
        review_decision_service=review_decision_service,
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
        change_payload={"_invalid": True},
        proposal_rationale="Test rationale.",
        change_evidence=("evidence-1",),
    )

    proposal.change_payload = {}

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Change Payload is required."
    assert traces[-1] is trace


def test_review_rejects_proposal_without_change_evidence():
    adapter, _, traces = create_adapter()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "statement": "Test statement",
        },
        proposal_rationale="Test rationale.",
        change_evidence=("evidence-1",),
    )

    proposal.change_evidence = ()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Change Evidence is required."
    assert traces[-1] is trace


def test_review_persists_proposal_before_evaluation():
    adapter, proposals, traces = create_adapter()

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.APPROVE
    assert trace.rationale == "Review approved."

    assert proposals.get_by_id(proposal.id) is proposal
    assert traces.get_by_id(trace.id) is trace

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

    adapter, proposal_repository, trace_repository = (
        create_adapter(
            knowledge_validation=knowledge_validation,
        )
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.APPROVE
    assert trace.rationale == "Review approved."

    assert knowledge_validation.proposals == [proposal]
    assert proposal_repository.get_by_id(proposal.id) is proposal
    assert trace_repository.get_by_id(trace.id) is trace


def test_review_rejects_proposal_when_repository_consistency_fails():
    knowledge_validation = InMemoryKnowledgeValidation(
        valid=True,
        rationale="Knowledge validation passed.",
    )

    repository_consistency = InMemoryRepositoryConsistency(
        consistent=False,
        rationale="Repository conflict detected.",
    )

    adapter, proposal_repository, trace_repository = (
        create_adapter(
            knowledge_validation=knowledge_validation,
            repository_consistency=repository_consistency,
        )
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Repository conflict detected."

    assert knowledge_validation.proposals == [proposal]
    assert repository_consistency.proposals == [proposal]
    assert proposal_repository.get_by_id(proposal.id) is proposal
    assert trace_repository.get_by_id(trace.id) is trace


def test_review_approves_proposal_after_all_validations():
    knowledge_validation = InMemoryKnowledgeValidation(
        valid=True,
        rationale="Knowledge validation passed.",
    )

    repository_consistency = InMemoryRepositoryConsistency(
        consistent=True,
        rationale="Repository consistency check passed.",
    )

    review_decision_service = InMemoryReviewDecisionService(
        decision=ReviewDecision.APPROVE,
        rationale="Review approved.",
    )

    adapter, proposal_repository, trace_repository = (
        create_adapter(
            knowledge_validation=knowledge_validation,
            repository_consistency=repository_consistency,
            review_decision_service=review_decision_service,
        )
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.APPROVE
    assert trace.rationale == "Review approved."

    assert knowledge_validation.proposals == [proposal]
    assert repository_consistency.proposals == [proposal]
    assert review_decision_service.proposals == [proposal]

    assert proposal_repository.get_by_id(proposal.id) is proposal
    assert trace_repository.get_by_id(trace.id) is trace


def test_review_requests_revision_after_all_validations():
    knowledge_validation = InMemoryKnowledgeValidation(
        valid=True,
        rationale="Knowledge validation passed.",
    )

    repository_consistency = InMemoryRepositoryConsistency(
        consistent=True,
        rationale="Repository consistency check passed.",
    )

    review_decision_service = InMemoryReviewDecisionService(
        decision=ReviewDecision.REQUEST_REVISION,
        rationale="Additional evidence is required.",
    )

    adapter, proposal_repository, trace_repository = (
        create_adapter(
            knowledge_validation=knowledge_validation,
            repository_consistency=repository_consistency,
            review_decision_service=review_decision_service,
        )
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REQUEST_REVISION
    assert trace.rationale == "Additional evidence is required."

    assert knowledge_validation.proposals == [proposal]
    assert repository_consistency.proposals == [proposal]
    assert review_decision_service.proposals == [proposal]

    assert proposal_repository.get_by_id(proposal.id) is proposal
    assert trace_repository.get_by_id(trace.id) is trace
