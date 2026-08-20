from abc import ABC, abstractmethod

from app.domain.entities.change_proposal import ChangeProposal


class RepositoryConsistency(ABC):
    """
    Port for checking a ChangeProposal against the current
    repository state.
    """

    @abstractmethod
    def check(
        self,
        proposal: ChangeProposal,
    ) -> tuple[bool, str]:
        """
        Check whether the proposal is consistent with the
        current repository state.

        Returns:
            (True, rationale) when the proposal is consistent.
            (False, rationale) when a repository conflict exists.
        """
        pass
