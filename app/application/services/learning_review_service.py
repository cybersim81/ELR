from app.application.security.authorization import (
    AuthorizationService,
)
from app.application.security.identity import IdentityContext
from app.application.security.permissions import Permission
from app.domain.entities.change_proposal import ChangeProposal
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.repositories.learning_review import LearningReview


class LearningReviewService:
    """
    Application service for Learning Review use cases.

    This service enforces reviewer authorization before
    delegating the review operation to the domain boundary.
    """

    def __init__(
        self,
        learning_review: LearningReview,
        authorization_service: AuthorizationService | None = None,
    ) -> None:
        self.learning_review = learning_review
        self.authorization_service = (
            authorization_service
            or AuthorizationService()
        )

    def review(
        self,
        proposal: ChangeProposal,
        reviewer: IdentityContext,
    ) -> ReviewDecisionTrace:
        self.authorization_service.require(
            reviewer,
            Permission.REVIEW_KNOWLEDGE,
        )

        return self.learning_review.review(
            proposal,
            str(reviewer.actor_id),
        )
