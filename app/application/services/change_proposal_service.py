from app.application.services.learning_review_service import (
    LearningReviewService,
)
from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)


class ChangeProposalService:
    """
    Application service for Change Proposal use cases.

    This service creates a ChangeProposal and submits it
    to the Learning Review boundary.
    """

    def __init__(
        self,
        learning_review_service: LearningReviewService,
    ):
        self.learning_review_service = learning_review_service

    def propose(
        self,
        change_type: ChangeType,
        change_payload: dict,
        proposal_rationale: str,
    ) -> ReviewDecisionTrace:
        """
        Create a ChangeProposal and submit it for Learning Review.
        """

        proposal = ChangeProposal(
            change_type=change_type,
            change_payload=change_payload,
            proposal_rationale=proposal_rationale,
        )

        return self.learning_review_service.review(proposal)
