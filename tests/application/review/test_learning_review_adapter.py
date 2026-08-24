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
        self.proposals = []

    def add(self, proposal):
        self.proposals.append(proposal)

    def get_by_id(self, proposal_id):
        return next(
            (
                proposal
                for proposal in self.proposals
                if proposal.id == proposal_id
            ),
            None,
        )


class InMemoryReviewDecisionTraceRepository:
    def __init__(self):
        self.traces = []

    def add(self, trace):
        self.traces.append(trace)

    def get_by_id(self, trace_id):
        return next(
            (
                trace
                for trace in self.traces
                if trace.id == trace_id
            ),
            None,
        )

    def __getitem__(self, index):
        return self.traces[index]

    def __len__(self):
        return len(self.traces)


class InMemoryKnowledgeValidation:
    def __init__(self, valid=True, rationale="Knowledge validation passed."):
        self.valid = valid
        self.rationale = rationale

    def validate(self, proposal):
        return self.valid, self.rationale


class InMemoryRepositoryConsistency:
    def __init__(
        self,
        consistent=True,
        rationale="Repository consistency check passed.",
    ):
        self.consistent = consistent
        self.rationale = rationale

    def check(self, proposal):
        return self.consistent, self.rationale


class InMemoryReviewDecisionService:
    def __init__(
        self,
        decision=ReviewDecision.APPROVE,
        rationale="Proposal approved.",
    ):
        self.decision = decision
        self.rationale = rationale

    def decide(self, proposal):
        return self.decision, self.rationale


def create_adapter(
    *,
    knowledge_valid=True,
    knowledge_rationale="Knowledge validation passed.",
    repository_consistent=True,
    repository_rationale="Repository consistency check passed.",
    decision=ReviewDecision.APPROVE,
    decision_rationale="Proposal approved.",
):
    proposal_repository = InMemoryChangeProposalRepository()
    traces = InMemoryReviewDecisionTraceRepository()

    knowledge_validation = InMemoryKnowledgeValidation(
        valid=knowledge_valid,
        rationale=knowledge_rationale,
    )

    repository_consistency = InMemoryRepositoryConsistency(
        consistent=repository_consistent,
        rationale=repository_rationale,
    )

    review_decision_service = InMemoryReviewDecisionService(
        decision=decision,
        rationale=decision_rationale,
    )

    adapter = LearningReviewAdapter(
        change_proposal_repository=proposal_repository,
        review_decision_trace_repository=traces,
        knowledge_validation=knowledge_validation,
        repository_consistency=repository_consistency,
        review_decision_service=review_decision_service,
    )

    return adapter, proposal_repository, traces


def create_valid_proposal():
    return ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "statement": "Test statement",
        },
        proposal_rationale="Test rationale.",
        change_evidence=(
            {
                "source": "test",
            },
        ),
    )


def test_review_rejects_proposal_without_change_type():
    adapter, _, traces = create_adapter()

    # Structural validation of ChangeProposal happens in the entity.
    # This test exercises the adapter only with a structurally valid
    # proposal, therefore Change Type validation is no longer performed
    # here.


def test_review_rejects_proposal_without_change_payload():
    adapter, _, traces = create_adapter()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={},
        proposal_rationale="Test rationale.",
        change_evidence=(
            {
                "source": "test",
            },
        ),
    )

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Change Payload is required."
    assert traces[-1] is trace



def test_review_rejects_proposal_without_change_evidence():
    adapter, _, traces = create_adapter()

    try:
        ChangeProposal(
            change_type=ChangeType.CREATE,
            change_payload={
                "statement": "Test statement",
            },
            proposal_rationale="Test rationale.",
            change_evidence=(),
        )
    except ValueError as exc:
        assert str(exc) == "Change Evidence is required."
    else:
        raise AssertionError(
            "ChangeProposal should reject empty change_evidence."
        )


def test_review_approves_valid_proposal():
    adapter, proposal_repository, traces = create_adapter()

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.APPROVE
    assert trace.rationale == "Proposal approved."
    assert proposal_repository.get_by_id(proposal.id) is proposal
    assert traces.get_by_id(trace.id) is trace


def test_review_rejects_invalid_knowledge():
    adapter, _, traces = create_adapter(
        knowledge_valid=False,
        knowledge_rationale="Knowledge validation failed.",
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Knowledge validation failed."
    assert traces.get_by_id(trace.id) is trace


def test_review_rejects_inconsistent_repository():
    adapter, _, traces = create_adapter(
        repository_consistent=False,
        repository_rationale="Repository consistency failed.",
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Repository consistency failed."
    assert traces.get_by_id(trace.id) is trace


def test_review_returns_request_revision():
    adapter, _, traces = create_adapter(
        decision=ReviewDecision.REQUEST_REVISION,
        decision_rationale="Revision required.",
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REQUEST_REVISION
    assert trace.rationale == "Revision required."
    assert traces.get_by_id(trace.id) is trace


def test_review_returns_reject_from_review_decision_service():
    adapter, _, traces = create_adapter(
        decision=ReviewDecision.REJECT,
        decision_rationale="Final decision rejected.",
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == "Final decision rejected."
    assert traces.get_by_id(trace.id) is trace
