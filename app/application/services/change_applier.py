from abc import ABC, abstractmethod

from app.domain.entities.change_proposal import ChangeProposal
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)


class ChangeApplier(ABC):
    """
    Application boundary for applying approved Change Proposals.

    Learning Review decides whether a Change Proposal may enter
    the ELR. ChangeApplier is responsible for the subsequent
    application of that approved proposal.

    ChangeApplier does not perform Learning Review.
    ChangeApplier does not generate proposals.
    ChangeApplier does not decide whether a proposal is valid.

    The application boundary therefore enforces the architectural
    separation:

        Change Proposal
                |
                v
        Learning Review
                |
             APPROVE
                |
                v
          Change Applier
                |
                v
               ELR
    """

    @abstractmethod
    def apply(
        self,
        proposal: ChangeProposal,
        review_trace: ReviewDecisionTrace,
        actor: str,
    ) -> object:
        """
        Apply an approved Change Proposal to the ELR.

        Implementations must reject any ReviewDecisionTrace that
        does not represent an APPROVE decision.

        Concrete change-type handling is introduced separately.
        """
        pass
