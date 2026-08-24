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


def test_change_proposal_service_creates_and_reviews_proposal():
    review_service = LearningReviewService(
        learning_review=StubLearningReview(),
    )

    service = ChangeProposalService(
        learning_review_service=review_service,
    )

    trace = service.propose(
        change_type=ChangeType.CREATE,
        change_payload={"statement": "Test statement"},
        proposal_rationale="Test proposal.",
        change_evidence=(
            {"type": "change", "source": "test"},
        ),
    )

    assert isinstance(trace, ReviewDecisionTrace)
    assert trace.decision is ReviewDecision.APPROVE
    assert trace.reviewer == "test-reviewer"

def test_change_proposal_service_requires_change_evidence():
    review_service = LearningReviewService(
        learning_review=StubLearningReview(),
    )

    service = ChangeProposalService(
        learning_review_service=review_service,
    )

    with pytest.raises(TypeError):
        service.propose(
            change_type=ChangeType.CREATE,
            change_payload={
                "statement": "Test statement",
            },
            proposal_rationale="Test rationale.",
        )


def test_change_proposal_service_creates_revision_with_provenance():
    review_service = LearningReviewService(
        learning_review=StubLearningReview(),
    )

    service = ChangeProposalService(
        learning_review_service=review_service,
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
    )

    assert isinstance(trace, ReviewDecisionTrace)
    assert trace.decision is ReviewDecision.APPROVE
