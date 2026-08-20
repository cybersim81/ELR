from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.repositories.change_proposal_repository import (
    ChangeProposalRepository,
)
from app.persistence.models.change_proposal_model import (
    ChangeProposalModel,
)


class SQLAlchemyChangeProposalRepository(
    ChangeProposalRepository,
):
    """
    SQLAlchemy implementation of ChangeProposalRepository.
    """

    def __init__(self, session: Session):
        self.session = session

    def add(
        self,
        proposal: ChangeProposal,
    ) -> None:
        model = ChangeProposalModel(
            id=proposal.id,
            change_type=proposal.change_type.value,
            change_payload=proposal.change_payload,
            proposal_rationale=proposal.proposal_rationale,
            created_at=proposal.created_at,
        )

        self.session.add(model)

    def get_by_id(
        self,
        proposal_id: UUID,
    ) -> ChangeProposal | None:
        model = self.session.get(
            ChangeProposalModel,
            proposal_id,
        )

        if model is None:
            return None

        return ChangeProposal(
            id=model.id,
            change_type=ChangeType(model.change_type),
            change_payload=model.change_payload,
            proposal_rationale=model.proposal_rationale,
            created_at=model.created_at,
        )
