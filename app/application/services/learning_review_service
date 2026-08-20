from app.domain.entities.change_proposal import ChangeProposal
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.repositories.learning_review import LearningReview


class LearningReviewService:
    """
    Application service for Learning Review use cases.

    This service coordinates the Learning Review boundary.
    It does not implement review semantics.
    """

    def __init__(
        self,
        learning_review: LearningReview,
    ):
        self.learning_review = learning_review

    def review(
        self,
        proposal: ChangeProposal,
    ) -> ReviewDecisionTrace:
        """
        Submit a Change Proposal to the Learning Review process.
        """

        return self.learning_review.review(proposal)
