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
from app.domain.repositories.repository_consistency import (
    RepositoryConsistency,
)
from app.domain.repositories.review_decision import (
    ReviewDecisionService,
)
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
        4. Final Review Decision
    """

    def __init__(
        self,
        change_proposal_repository: ChangeProposalRepository,
        review_decision_trace_repository: ReviewDecisionTraceRepository,
        knowledge_validation: KnowledgeValidation,
        repository_consistency: RepositoryConsistency,
        review_decision_service: ReviewDecisionService,
        reviewer: str = "learning-review",
    ):
        self.change_proposal_repository = (
            change_proposal_repository
        )
        self.review_decision_trace_repository = (
            review_decision_trace_repository
        )
        self.knowledge_validation = knowledge_validation
        self.repository_consistency = repository_consistency
        self.review_decision_service = review_decision_service
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


def test_review_rejects_proposal_from_final_decision_service():
    knowledge_validation = InMemoryKnowledgeValidation(
        valid=True,
        rationale="Knowledge validation passed.",
    )

    repository_consistency = InMemoryRepositoryConsistency(
        consistent=True,
        rationale="Repository consistency check passed.",
    )

    review_decision_service = InMemoryReviewDecisionService(
        decision=ReviewDecision.REJECT,
        rationale="Proposal does not meet review criteria.",
    )

    adapter, proposal_repository, trace_repository = (
        create_adapter(
            knowledge_validation=knowledge_validation,
            repository_consistency=repository_consistency,
            review_decision_service=review_decision_service,
        )
    )

    proposal = create_valid_proposal()

    trace = adapter.review(proposal)

    assert trace.decision is ReviewDecision.REJECT
    assert trace.rationale == (
        "Proposal does not meet review criteria."
    )

    assert knowledge_validation.proposals == [proposal]
    assert repository_consistency.proposals == [proposal]
    assert review_decision_service.proposals == [proposal]

    assert proposal_repository.get_by_id(proposal.id) is proposal
    assert trace_repository.get_by_id(trace.id) is trace
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

        repository_consistent, rationale = (
            self.repository_consistency.check(proposal)
        )

        if not repository_consistent:
            return (
                ReviewDecision.REJECT,
                rationale,
            )

        return self.review_decision_service.decide(proposal)

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
