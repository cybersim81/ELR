from uuid import UUID

from app.domain.entities.change_proposal import (
ChangeProposal,
ChangeType,
)

def test_create_change_proposal_contains_required_fields():
proposal = ChangeProposal(
change_type=ChangeType.CREATE,
change_payload={
"anchor": "take + photo",
"knowledge_statement": "Per scattare una fotografia si usa take + photo.",
"category_id": "category-id",
},
proposal_rationale="La conoscenza non è rappresentata nel repository.",
change_evidence=(
{"trigger": "linguistic_error"},
),
change_metadata={
"origin": "KEP",
},
)

assert isinstance(proposal.id, UUID)
assert proposal.change_type is ChangeType.CREATE
assert proposal.change_payload["anchor"] == "take + photo"
assert proposal.proposal_rationale
assert proposal.change_evidence == (
    {"trigger": "linguistic_error"},
)
assert proposal.change_metadata["origin"] == "KEP"

def test_change_proposal_supports_all_change_types():
for change_type in ChangeType:
proposal = ChangeProposal(
change_type=change_type,
change_payload={},
proposal_rationale="test",
)

    assert proposal.change_type is change_type

def test_change_proposal_is_immutable():
proposal = ChangeProposal(
change_type=ChangeType.CREATE,
change_payload={},
proposal_rationale="test",
)

try:
    proposal.change_type = ChangeType.UPDATE
except AttributeError:
    pass
else:
    raise AssertionError("ChangeProposal must be immutable")

def test_change_evidence_defaults_to_empty():
proposal = ChangeProposal(
change_type=ChangeType.UPDATE,
change_payload={},
proposal_rationale="test",
)

assert proposal.change_evidence == ()
assert proposal.change_metadata == {}
