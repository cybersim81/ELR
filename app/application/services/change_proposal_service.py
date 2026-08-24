from uuid import UUID

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

    This service creates Change Proposals and submits them
    to the Learning Review boundary.

    It does not modify the ELR repository directly.
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
        change_evidence: tuple[dict, ...],
        change_metadata: dict | None = None,
    ) -> ReviewDecisionTrace:
        """
        Create a new Change Proposal and submit it
        to Learning Review.
        """

        proposal = ChangeProposal(
            change_type=change_type,
            change_payload=change_payload,
            proposal_rationale=proposal_rationale,
            change_evidence=change_evidence,
            change_metadata=change_metadata or {},
        )

        return self.learning_review_service.review(proposal)

    def revise(
        self,
        previous_proposal: ChangeProposal,
        previous_trace: ReviewDecisionTrace,
        change_payload: dict,
        proposal_rationale: str,
        change_evidence: tuple[dict, ...],
        change_metadata: dict | None = None,
    ) -> ReviewDecisionTrace:
        """
        Create a new revision of a Change Proposal after
        REQUEST_REVISION.

        The revised proposal preserves provenance to both:
        - the previous Change Proposal;
        - the Review Decision Trace that requested revision.
        """

        proposal = ChangeProposal(
            change_type=previous_proposal.change_type,
            change_payload=change_payload,
            proposal_rationale=proposal_rationale,
            change_evidence=change_evidence,
            change_metadata=change_metadata or {},
            previous_proposal_id=previous_proposal.id,
            previous_review_trace_id=previous_trace.id,
            revision_number=(
                previous_proposal.revision_number + 1
            ),
        )

        return self.learning_review_service.review(proposal)
