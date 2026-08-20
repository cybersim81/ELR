from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.persistence import database
from app.persistence.repositories.change_proposal_repository import (
    SQLAlchemyChangeProposalRepository,
)


def test_add_persists_change_proposal():
    session = database.SessionFactory()

    try:
        proposal = ChangeProposal(
            change_type=ChangeType.CREATE,
            change_payload={"statement": "Test statement"},
            proposal_rationale="Test rationale.",
        )

        repository = SQLAlchemyChangeProposalRepository(session)

        repository.add(proposal)
        session.flush()

        loaded = repository.get_by_id(proposal.id)

        assert loaded is not None
        assert loaded.id == proposal.id
        assert loaded.change_type is ChangeType.CREATE
        assert loaded.change_payload == {
            "statement": "Test statement",
        }
        assert loaded.proposal_rationale == "Test rationale."
    finally:
        session.rollback()
        session.close()
