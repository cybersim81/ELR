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


def test_learning_review_service_delegates_to_review_boundary():
    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={},
        proposal_rationale="Test proposal.",
    )

    service = LearningReviewService(
        learning_review=StubLearningReview(),
    )

    trace = service.review(proposal)

    assert isinstance(trace, ReviewDecisionTrace)
    assert trace.proposal_id == proposal.id
    assert trace.decision is ReviewDecision.APPROVE
