from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.entities.review_decision import ReviewDecision
from app.domain.repositories.review_decision import (
    ReviewDecisionService,
)


class InMemoryReviewDecisionService(ReviewDecisionService):
    def __init__(
        self,
        decision=ReviewDecision.APPROVE,
        rationale="Review approved.",
    ):
        self.decision = decision
        self.rationale = rationale
        self.proposals = []

    def decide(
        self,
        proposal: ChangeProposal,
    ) -> tuple[ReviewDecision, str]:
        self.proposals.append(proposal)

        return self.decision, self.rationale


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


def test_review_decision_service_approves_proposal():
    service = InMemoryReviewDecisionService(
        decision=ReviewDecision.APPROVE,
        rationale="Review approved.",
    )

    proposal = create_proposal()

    decision, rationale = service.decide(proposal)

    assert decision is ReviewDecision.APPROVE
    assert rationale == "Review approved."
    assert service.proposals == [proposal]


def test_review_decision_service_requests_revision():
    service = InMemoryReviewDecisionService(
        decision=ReviewDecision.REQUEST_REVISION,
        rationale="Additional evidence is required.",
    )

    proposal = create_proposal()

    decision, rationale = service.decide(proposal)

    assert decision is ReviewDecision.REQUEST_REVISION
    assert rationale == "Additional evidence is required."
    assert service.proposals == [proposal]


def test_review_decision_service_rejects_proposal():
    service = InMemoryReviewDecisionService(
        decision=ReviewDecision.REJECT,
        rationale="Review rejected.",
    )

    proposal = create_proposal()

    decision, rationale = service.decide(proposal)

    assert decision is ReviewDecision.REJECT
    assert rationale == "Review rejected."
    assert service.proposals == [proposal]
