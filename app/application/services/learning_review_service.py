import pytest
from uuid import uuid4

from app.application.errors import UnauthorizedOperation
from app.application.security.identity import IdentityContext
from app.application.security.roles import Role
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
        actor_type="Human Reviewer",
        roles=frozenset({role.value}),
    )


class StubLearningReview(LearningReview):
    def __init__(self):
        self.reviewer = None

    def review(
        self,
        proposal: ChangeProposal,
        reviewer: IdentityContext,
    ) -> ReviewDecisionTrace:
        self.reviewer = reviewer

        return ReviewDecisionTrace(
            proposal_id=proposal.id,
            decision=ReviewDecision.APPROVE,
            rationale="Approved for testing.",
            reviewer=str(reviewer.actor_id),
        )


def test_learning_review_service_delegates_authorized_review():
    learning_review = StubLearningReview()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={},
        proposal_rationale="Test proposal.",
    )

    reviewer = make_identity(
        Role.KNOWLEDGE_REVIEWER,
    )

    service = LearningReviewService(
        learning_review=learning_review,
    )

    trace = service.review(
        proposal,
        reviewer,
    )

    assert isinstance(trace, ReviewDecisionTrace)
    assert trace.proposal_id == proposal.id
    assert trace.decision is ReviewDecision.APPROVE
    assert learning_review.reviewer is reviewer


def test_learning_review_service_rejects_unauthorized_reviewer():
    learning_review = StubLearningReview()

    proposal = ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={},
        proposal_rationale="Test proposal.",
    )

    reviewer = make_identity(
        Role.KNOWLEDGE_PRODUCER,
    )

    service = LearningReviewService(
        learning_review=learning_review,
    )

    with pytest.raises(UnauthorizedOperation):
        service.review(
            proposal,
            reviewer,
        )

    assert learning_review.reviewer is None
