import pytest
from uuid import uuid4

from app.application.security.identity import IdentityContext
from app.application.security.roles import Role
from app.application.services.change_proposal_service import (
    ChangeProposalService,
)
from app.application.services.learning_review_service import (
    LearningReviewService,
)
from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.repositories.learning_review import LearningReview


def make_identity(role: Role) -> IdentityContext:
    return IdentityContext(
        actor_id=uuid4(),
        actor_type="Human",
        roles=frozenset({role.value}),
    )


class StubLearningReview(LearningReview):
    def __init__(self):
        self.reviewer = None

    def review(
        self,
        proposal: ChangeProposal,
        reviewer: str,
    ) -> ReviewDecisionTrace:
        self.reviewer = reviewer

        return ReviewDecisionTrace(
            proposal_id=proposal.id,
            decision=ReviewDecision.APPROVE,
            rationale="Approved for testing.",
            reviewer=reviewer,
        )


class StubChangeApplier:
    def __init__(self):
        self.calls = []

    def apply(
        self,
        proposal: ChangeProposal,
        review_trace: ReviewDecisionTrace,
        actor: str,
    ):
        self.calls.append(
            (
                proposal,
                review_trace,
                actor,
            )
        )


class RejectingLearningReview(LearningReview):
    def __init__(self, decision, rationale):
        self.decision = decision
        self.rationale = rationale

    def review(
        self,
        proposal: ChangeProposal,
        reviewer: str,
    ) -> ReviewDecisionTrace:
        return ReviewDecisionTrace(
            proposal_id=proposal.id,
            decision=self.decision,
            rationale=self.rationale,
            reviewer=reviewer,
        )


def test_change_proposal_service_separates_proposer_and_reviewer():
    review = StubLearningReview()

    review_service = LearningReviewService(
        learning_review=review,
    )

    change_applier = StubChangeApplier()

    service = ChangeProposalService(
        learning_review_service=review_service,
        change_applier=change_applier,
    )

    proposer = make_identity(
        Role.KNOWLEDGE_PRODUCER,
    )
    reviewer = make_identity(
        Role.KNOWLEDGE_REVIEWER,
    )

    trace = service.propose(
        change_type=ChangeType.CREATE,
        change_payload={"statement": "Test statement"},
        proposal_rationale="Test proposal.",
        change_evidence=(
            {"type": "change", "source": "test"},
        ),
        proposer=proposer,
        reviewer=reviewer,
    )

    assert isinstance(trace, ReviewDecisionTrace)
    assert trace.decision is ReviewDecision.APPROVE

    assert review.reviewer == str(
        reviewer.actor_id,
    )
    assert len(change_applier.calls) == 1

    proposal, applied_trace, actor = (
        change_applier.calls[0]
    )

    assert proposal.change_type is ChangeType.CREATE
    assert applied_trace is trace
    assert actor == str(reviewer.actor_id)


def test_change_proposal_service_requires_change_evidence():
    review_service = LearningReviewService(
        learning_review=StubLearningReview(),
    )

    change_applier = StubChangeApplier()

    service = ChangeProposalService(
        learning_review_service=review_service,
        change_applier=change_applier,
    )

    proposer = make_identity(
        Role.KNOWLEDGE_PRODUCER,
    )
    reviewer = make_identity(
        Role.KNOWLEDGE_REVIEWER,
    )

    with pytest.raises(TypeError):
        service.propose(
            change_type=ChangeType.CREATE,
            change_payload={
                "statement": "Test statement",
            },
            proposal_rationale="Test rationale.",
            proposer=proposer,
            reviewer=reviewer,
        )


def test_change_proposal_service_creates_revision_with_provenance():
    review_service = LearningReviewService(
        learning_review=StubLearningReview(),
    )

    change_applier = StubChangeApplier()

    service = ChangeProposalService(
        learning_review_service=review_service,
        change_applier=change_applier,
    )

    previous = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={"statement": "Original"},
        proposal_rationale="Original proposal.",
        change_evidence=(
            {"type": "change", "source": "test"},
        ),
    )

    previous_trace = ReviewDecisionTrace(
        proposal_id=previous.id,
        decision=ReviewDecision.REQUEST_REVISION,
        rationale="Additional evidence required.",
        reviewer="test-reviewer",
    )

    proposer = make_identity(
        Role.KNOWLEDGE_PRODUCER,
    )
    reviewer = make_identity(
        Role.KNOWLEDGE_REVIEWER,
    )

    trace = service.revise(
        previous_proposal=previous,
        previous_trace=previous_trace,
        change_payload={"statement": "Revised"},
        proposal_rationale="Revised proposal.",
        change_evidence=(
            {"type": "change", "source": "test-revised"},
        ),
        proposer=proposer,
        reviewer=reviewer,
    )

    assert isinstance(trace, ReviewDecisionTrace)
    assert trace.decision is ReviewDecision.APPROVE

    assert len(change_applier.calls) == 1

    proposal, applied_trace, actor = (
        change_applier.calls[0]
    )

    assert proposal.previous_proposal_id == previous.id
    assert proposal.previous_review_trace_id == previous_trace.id
    assert proposal.revision_number == 2
    assert applied_trace is trace
    assert actor == str(reviewer.actor_id)


def test_change_proposal_service_does_not_apply_rejected_proposal():
    review_service = LearningReviewService(
        learning_review=RejectingLearningReview(
            decision=ReviewDecision.REJECT,
            rationale="Rejected for testing.",
        ),
    )

    change_applier = StubChangeApplier()

    service = ChangeProposalService(
        learning_review_service=review_service,
        change_applier=change_applier,
    )

    proposer = make_identity(
        Role.KNOWLEDGE_PRODUCER,
    )
    reviewer = make_identity(
        Role.KNOWLEDGE_REVIEWER,
    )

    trace = service.propose(
        change_type=ChangeType.CREATE,
        change_payload={"statement": "Test statement"},
        proposal_rationale="Test proposal.",
        change_evidence=(
            {"type": "change", "source": "test"},
        ),
        proposer=proposer,
        reviewer=reviewer,
    )

    assert trace.decision is ReviewDecision.REJECT
    assert change_applier.calls == []


def test_change_proposal_service_does_not_apply_revision_request():
    review_service = LearningReviewService(
        learning_review=RejectingLearningReview(
            decision=ReviewDecision.REQUEST_REVISION,
            rationale="Revision required.",
        ),
    )

    change_applier = StubChangeApplier()

    service = ChangeProposalService(
        learning_review_service=review_service,
        change_applier=change_applier,
    )

    proposer = make_identity(
        Role.KNOWLEDGE_PRODUCER,
    )
    reviewer = make_identity(
        Role.KNOWLEDGE_REVIEWER,
    )

    trace = service.propose(
        change_type=ChangeType.CREATE,
        change_payload={"statement": "Test statement"},
        proposal_rationale="Test proposal.",
        change_evidence=(
            {"type": "change", "source": "test"},
        ),
        proposer=proposer,
        reviewer=reviewer,
    )

    assert trace.decision is ReviewDecision.REQUEST_REVISION
    assert change_applier.calls == []
