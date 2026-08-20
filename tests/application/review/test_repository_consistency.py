from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.repositories.repository_consistency import (
    RepositoryConsistency,
)


class InMemoryRepositoryConsistency(RepositoryConsistency):
    def __init__(
        self,
        consistent=True,
        rationale="Repository consistency check passed.",
    ):
        self.consistent = consistent
        self.rationale = rationale
        self.proposals = []

    def check(
        self,
        proposal: ChangeProposal,
    ) -> tuple[bool, str]:
        self.proposals.append(proposal)

        return self.consistent, self.rationale


def create_proposal():
    return ChangeProposal(
        change_type=ChangeType.CREATE,
        change_payload={
            "anchor": "weever",
            "statement": "weever → tracina",
        },
        proposal_rationale="Candidate linguistic knowledge.",
        change_evidence=("evidence-1",),
    )


def test_repository_consistency_accepts_consistent_proposal():
    checker = InMemoryRepositoryConsistency()

    proposal = create_proposal()

    consistent, rationale = checker.check(proposal)

    assert consistent is True
    assert rationale == "Repository consistency check passed."
    assert checker.proposals == [proposal]


def test_repository_consistency_rejects_inconsistent_proposal():
    checker = InMemoryRepositoryConsistency(
        consistent=False,
        rationale="Repository conflict detected.",
    )

    proposal = create_proposal()

    consistent, rationale = checker.check(proposal)

    assert consistent is False
    assert rationale == "Repository conflict detected."
    assert checker.proposals == [proposal]
