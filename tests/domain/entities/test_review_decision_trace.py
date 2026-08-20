from datetime import datetime, timezone
from uuid import UUID

from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)


def test_review_decision_trace_contains_required_fields():
    proposal_id = UUID("00000000-0000-0000-0000-000000000001")

    trace = ReviewDecisionTrace(
        proposal_id=proposal_id,
        decision=ReviewDecision.APPROVE,
        rationale="La proposta è supportata da evidenza sufficiente.",
        reviewer="reviewer-1",
    )

    assert isinstance(trace.id, UUID)
    assert trace.proposal_id == proposal_id
    assert trace.decision is ReviewDecision.APPROVE
    assert trace.rationale
    assert trace.reviewer


def test_review_decision_trace_records_all_review_decisions():
    proposal_id = UUID("00000000-0000-0000-0000-000000000001")

    for decision in ReviewDecision:
        trace = ReviewDecisionTrace(
            proposal_id=proposal_id,
            decision=decision,
            rationale="test",
            reviewer="reviewer-1",
        )

        assert trace.decision is decision


def test_review_decision_trace_has_utc_timestamp():
    trace = ReviewDecisionTrace(
        proposal_id=UUID("00000000-0000-0000-0000-000000000001"),
        decision=ReviewDecision.REJECT,
        rationale="test",
        reviewer="reviewer-1",
    )

    assert isinstance(trace.created_at, datetime)
    assert trace.created_at.tzinfo == timezone.utc


def test_review_decision_trace_is_immutable():
    trace = ReviewDecisionTrace(
        proposal_id=UUID("00000000-0000-0000-0000-000000000001"),
        decision=ReviewDecision.REQUEST_REVISION,
        rationale="test",
        reviewer="reviewer-1",
    )

    try:
        trace.decision = ReviewDecision.APPROVE
    except AttributeError:
        pass
    else:
        raise AssertionError("ReviewDecisionTrace must be immutable")
