from datetime import datetime, timezone

from app.domain.entities.change_proposal import ChangeProposal
from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.repositories.change_proposal_repository import (
    ChangeProposalRepository,
)
from app.domain.repositories.knowledge_validation import (
    KnowledgeValidation,
)
from app.domain.repositories.learning_review import LearningReview
from app.domain.repositories.review_decision_trace_repository import (
    ReviewDecisionTraceRepository,
)


class LearningReviewAdapter(LearningReview):
    """
    Concrete Learning Review boundary.

    Review flow:
        1. Proposal Validation
        2. Knowledge Validation
        3. Repository Consistency Check
        4. Decision
    """

    def __init__(
        self,
        change_proposal_repository: ChangeProposalRepository,
        review_decision_trace_repository: ReviewDecisionTraceRepository,
        knowledge_validation: KnowledgeValidation,
        reviewer: str = "learning-review",
    ):
        self.change_proposal_repository = (
            change_proposal_repository
        )
        self.review_decision_trace_repository = (
            review_decision_trace_repository
        )
        self.knowledge_validation = knowledge_validation
        self.reviewer = reviewer

    def review(
        self,
        proposal: ChangeProposal,
    ) -> ReviewDecisionTrace:
        self.change_proposal_repository.add(proposal)

        decision, rationale = self._evaluate(proposal)

        trace = ReviewDecisionTrace(
            proposal_id=proposal.id,
            decision=decision,
            rationale=rationale,
            reviewer=self.reviewer,
            created_at=datetime.now(timezone.utc),
        )

        self.review_decision_trace_repository.add(trace)

        return trace

    def _evaluate(
        self,
        proposal: ChangeProposal,
    ) -> tuple[ReviewDecision, str]:
        validation_error = self._validate_proposal(proposal)

        if validation_error is not None:
            return (
                ReviewDecision.REJECT,
                validation_error,
            )

        knowledge_valid, rationale = (
            self.knowledge_validation.validate(proposal)
        )

        if not knowledge_valid:
            return (
                ReviewDecision.REJECT,
                rationale,
            )

        return self._evaluate_after_knowledge_validation(
            proposal
        )

    def _validate_proposal(
        self,
        proposal: ChangeProposal,
    ) -> str | None:
        if proposal.change_type is None:
            return "Change Type is required."

        if not proposal.change_payload:
            return "Change Payload is required."

        if not proposal.change_evidence:
            return "Change Evidence is required."

        return None

    def _evaluate_after_knowledge_validation(
        self,
        proposal: ChangeProposal,
    ) -> tuple[ReviewDecision, str]:
        raise NotImplementedError(
            "Repository Consistency Check and final "
            "Review Decision are not implemented yet."
        )
