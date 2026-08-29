from abc import ABC, abstractmethod

from app.domain.entities.change_proposal import ChangeProposal
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)


class LearningReview(ABC):
    """
    Contract for the Learning Review process.

    The implementation owns review semantics.
    Application services only coordinate the process.
    """

    @abstractmethod
    def review(
        self,
        proposal: ChangeProposal,
        reviewer: str,
    ) -> ReviewDecisionTrace:
        pass
