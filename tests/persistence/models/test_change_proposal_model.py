from uuid import uuid4

from app.persistence.models.change_proposal_model import (
    ChangeProposalModel,
)


def test_change_proposal_model_has_expected_table_name():
    assert ChangeProposalModel.__tablename__ == "change_proposals"


def test_change_proposal_model_accepts_expected_fields():
    proposal_id = uuid4()

    model = ChangeProposalModel(
        id=proposal_id,
        change_type="CREATE",
        change_payload={"statement": "Test statement"},
        proposal_rationale="Test rationale.",
        change_evidence=["evidence-1"],
        change_metadata={"source": "test"},
    )

    assert model.id == proposal_id
    assert model.change_type == "CREATE"
    assert model.change_payload == {
        "statement": "Test statement",
    }
    assert model.proposal_rationale == "Test rationale."
    assert model.change_evidence == ["evidence-1"]
    assert model.change_metadata == {"source": "test"}
