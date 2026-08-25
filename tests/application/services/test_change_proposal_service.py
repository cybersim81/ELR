import pytest

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


class StubLearningReview(LearningReview):
    def review(
        self,
        proposal: ChangeProposal,
    ) -> ReviewDecisionTrace:
        return ReviewDecisionTrace(
            proposal_id=proposal.id,
            decision=ReviewDecision.APPROVE,
            rationale="Approved for testing.",
            reviewer="test-reviewer",
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

def test_change_proposal_service_creates_and_reviews_proposal():
    review_service = LearningReviewService(
        learning_review=StubLearningReview(),
    )

    change_applier = StubChangeApplier()

    service = ChangeProposalService(
        learning_review_service=review_service,
        change_applier=change_applier,
    )

    trace = service.propose(
        change_type=ChangeType.CREATE,
        change_payload={"statement": "Test statement"},
        proposal_rationale="Test proposal.",
        change_evidence=(
            {"type": "change", "source": "test"},
        ),
        actor="test-actor",
    )

    assert isinstance(trace, ReviewDecisionTrace)
    assert trace.decision is ReviewDecision.APPROVE
    assert trace.reviewer == "test-reviewer"

    assert len(change_applier.calls) == 1

    proposal, applied_trace, actor = change_applier.calls[0]

    assert proposal.change_type is ChangeType.CREATE
    assert proposal.change_payload == {
        "statement": "Test statement",
    }
    assert applied_trace is trace
    assert actor == "test-actor"

def test_change_proposal_service_requires_change_evidence():
    review_service = LearningReviewService(
        learning_review=StubLearningReview(),
    )

    change_applier = StubChangeApplier()

    service = ChangeProposalService(
        learning_review_service=review_service,
        change_applier=change_applier,
    )

    with pytest.raises(TypeError):
        service.propose(
            change_type=ChangeType.CREATE,
            change_payload={
                "statement": "Test statement",
            },
            proposal_rationale="Test rationale.",
            actor="test-actor",
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

    trace = service.revise(
        previous_proposal=previous,
        previous_trace=previous_trace,
        change_payload={"statement": "Revised"},
        proposal_rationale="Revised proposal.",
        change_evidence=(
            {"type": "change", "source": "test-revised"},
        ),
        actor="test-actor",
    )

    assert isinstance(trace, ReviewDecisionTrace)
    assert trace.decision is ReviewDecision.APPROVE

    assert len(change_applier.calls) == 1

    proposal, applied_trace, actor = change_applier.calls[0]

    assert proposal.previous_proposal_id == previous.id
    assert proposal.previous_review_trace_id == previous_trace.id
    assert proposal.revision_number == 2
    assert applied_trace is trace
    assert actor == "test-actor"
