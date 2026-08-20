from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.domain.entities.review_decision import ReviewDecision


@dataclass(frozen=True)
class ReviewDecisionTrace:
    """
    Immutable trace of a Learning Review decision.

    The trace records the decision and its normative justification.
    It does not perform the review itself.
    """

    proposal_id: UUID
    decision: ReviewDecision
    rationale: str
    reviewer: str
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    id: UUID = field(default_factory=uuid4)
