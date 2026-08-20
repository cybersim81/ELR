from datetime import datetime, timezone

from app.domain.entities.change_proposal import ChangeProposal
from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.repositories.change_proposal_repository import (
    ChangeProposalRepository,
)
from app.domain.repositories.learning_review import LearningReview
from app.domain.repositories.review_decision_trace_repository import (
    ReviewDecisionTraceRepository,
)


class LearningReviewAdapter(LearningReview):
    """
    Concrete boundary for the Learning Review process.

    The adapter owns orchestration and persistence of the resulting
    ReviewDecisionTrace. The actual normative decision rule is kept
    in _evaluate(), so it can be replaced with the specification-driven
    Review semantics without changing the persistence boundary.
    """

    def __init__(
        self,
        change_proposal_repository: ChangeProposalRepository,
        review_decision_trace_repository: ReviewDecisionTraceRepository,
        reviewer: str = "learning-review",
    ):
        self.change_proposal_repository = (
            change_proposal_repository
        )
        self.review_decision_trace_repository = (
            review_decision_trace_repository
        )
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
        raise NotImplementedError(
            "Normative Learning Review evaluation is not implemented yet."
        )
