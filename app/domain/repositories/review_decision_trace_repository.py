from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)


class ReviewDecisionTraceRepository(ABC):
    """
    Repository contract for ReviewDecisionTrace persistence.
    """

    @abstractmethod
    def add(
        self,
        trace: ReviewDecisionTrace,
    ) -> None:
        pass

    @abstractmethod
    def get_by_id(
        self,
        trace_id: UUID,
    ) -> ReviewDecisionTrace | None:
        pass

    @abstractmethod
    def get_by_proposal_id(
        self,
        proposal_id: UUID,
    ) -> list[ReviewDecisionTrace]:
        pass
