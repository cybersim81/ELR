from uuid import UUID

import pytest

from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.repositories.learning_review import (
    LearningReview,
)


class StubLearningReview(LearningReview):
    def review(
        self,
        proposal: ChangeProposal,
    ) -> ReviewDecisionTrace:
        return ReviewDecisionTrace(
            proposal_id=proposal.id,
            decision=ReviewDecision.APPROVE,
            rationale="Stub review.",
            reviewer="test-reviewer",
        )


def test_learning_review_is_an_abstract_contract():
    with pytest.raises(TypeError):
        LearningReview()


def test_learning_review_returns_review_decision_trace():
    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={},
        proposal_rationale="Test proposal.",
    )

    reviewer = StubLearningReview()

    trace = reviewer.review(proposal)

    assert isinstance(trace, ReviewDecisionTrace)
    assert trace.proposal_id == proposal.id
    assert trace.decision is ReviewDecision.APPROVE
    assert isinstance(trace.proposal_id, UUID)
