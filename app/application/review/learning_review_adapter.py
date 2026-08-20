from app.domain.entities.change_proposal import ChangeProposal
from app.domain.entities.review_decision_trace import ReviewDecisionTrace
from app.domain.repositories.learning_review import LearningReview


class LearningReviewAdapter(LearningReview):
    """
    Concrete boundary for the Learning Review process.

    Review semantics must be implemented here according to the
    Learning Review Specification. This adapter must not be used
    as a placeholder that invents approval/rejection policy.
    """

    def review(
        self,
        proposal: ChangeProposal,
    ) -> ReviewDecisionTrace:
        raise NotImplementedError(
            "Learning Review semantics are not implemented yet."
        )
