from abc import ABC, abstractmethod

from app.domain.entities.change_proposal import ChangeProposal


class KnowledgeValidation(ABC):
    """
    Port for validating a ChangeProposal against existing knowledge.

    The concrete implementation is responsible for determining whether
    the proposal is compatible with the authoritative knowledge model.
    """

    @abstractmethod
    def validate(
        self,
        proposal: ChangeProposal,
    ) -> tuple[bool, str]:
        """
        Validate the proposal against existing knowledge.

        Returns:
            (True, rationale) when knowledge validation succeeds.
            (False, rationale) when the proposal must not proceed.
        """
        pass
