from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.repositories.knowledge_validation import (
    KnowledgeValidation,
)


class InMemoryKnowledgeValidation(KnowledgeValidation):
    def __init__(
        self,
        valid: bool = True,
        rationale: str = "Knowledge validation passed.",
    ):
        self.valid = valid
        self.rationale = rationale
        self.proposals = []

    def validate(
        self,
        proposal: ChangeProposal,
    ) -> tuple[bool, str]:
        self.proposals.append(proposal)

        return self.valid, self.rationale


def create_proposal():
    return ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "statement": "weever → tracina",
        },
        proposal_rationale="Candidate linguistic knowledge.",
        change_evidence=("evidence-1",),
    )


def test_knowledge_validation_accepts_valid_proposal():
    validator = InMemoryKnowledgeValidation()

    proposal = create_proposal()

    valid, rationale = validator.validate(proposal)

    assert valid is True
    assert rationale == "Knowledge validation passed."
    assert validator.proposals == [proposal]


def test_knowledge_validation_rejects_invalid_proposal():
    validator = InMemoryKnowledgeValidation(
        valid=False,
        rationale="Knowledge conflict detected.",
    )

    proposal = create_proposal()

    valid, rationale = validator.validate(proposal)

    assert valid is False
    assert rationale == "Knowledge conflict detected."
    assert validator.proposals == [proposal]
