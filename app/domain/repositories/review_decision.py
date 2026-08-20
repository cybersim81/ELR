from abc import ABC, abstractmethod

from app.domain.entities.change_proposal import ChangeProposal
from app.domain.entities.review_decision import ReviewDecision


class ReviewDecisionService(ABC):
    """
    Port for determining the final decision for a proposal that
    passed Proposal Validation, Knowledge Validation and
    Repository Consistency.
    """

    @abstractmethod
    def decide(
        self,
        proposal: ChangeProposal,
    ) -> tuple[ReviewDecision, str]:
        """
        Determine the final review decision.

        Returns:
            The decision and its rationale.
        """
        pass
