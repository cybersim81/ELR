from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.repositories.review_decision_trace_repository import (
    ReviewDecisionTraceRepository,
)
from app.persistence.models.review_decision_trace_model import (
    ReviewDecisionTraceModel,
)


class SQLAlchemyReviewDecisionTraceRepository(
    ReviewDecisionTraceRepository,
):
    """
    SQLAlchemy implementation of ReviewDecisionTraceRepository.
    """

    def __init__(self, session: Session):
        self.session = session

    def add(
        self,
        trace: ReviewDecisionTrace,
    ) -> None:
        model = ReviewDecisionTraceModel(
            id=trace.id,
            proposal_id=trace.proposal_id,
            decision=trace.decision.value,
            rationale=trace.rationale,
            reviewer=trace.reviewer,
            created_at=trace.created_at,
        )

        self.session.add(model)

    def get_by_id(
        self,
        trace_id: UUID,
    ) -> ReviewDecisionTrace | None:
        model = self.session.get(
            ReviewDecisionTraceModel,
            trace_id,
        )

        if model is None:
            return None

        return ReviewDecisionTrace(
            id=model.id,
            proposal_id=model.proposal_id,
            decision=ReviewDecision(model.decision),
            rationale=model.rationale,
            reviewer=model.reviewer,
            created_at=model.created_at,
        )

    def get_by_proposal_id(
        self,
        proposal_id: UUID,
    ) -> list[ReviewDecisionTrace]:
        statement = (
            select(ReviewDecisionTraceModel)
            .where(
                ReviewDecisionTraceModel.proposal_id
                == proposal_id
            )
            .order_by(
                ReviewDecisionTraceModel.created_at.asc()
            )
        )

        models = self.session.scalars(statement).all()

        return [
            ReviewDecisionTrace(
                id=model.id,
                proposal_id=model.proposal_id,
                decision=ReviewDecision(model.decision),
                rationale=model.rationale,
                reviewer=model.reviewer,
                created_at=model.created_at,
            )
            for model in models
        ]
