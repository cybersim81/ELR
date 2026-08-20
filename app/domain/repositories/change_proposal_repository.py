from abc import ABC, abstractmethod

from app.domain.entities.change_proposal import ChangeProposal


class ChangeProposalRepository(ABC):
    """
    Repository contract for ChangeProposal persistence.
    """

    @abstractmethod
    def add(
        self,
        proposal: ChangeProposal,
    ) -> None:
        pass

    @abstractmethod
    def get_by_id(
        self,
        proposal_id,
    ) -> ChangeProposal | None:
        pass
