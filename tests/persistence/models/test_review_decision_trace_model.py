from datetime import datetime, timezone
from uuid import uuid4

from app.persistence.models.review_decision_trace_model import (
    ReviewDecisionTraceModel,
)


def test_review_decision_trace_model_has_expected_table_name():
    assert (
        ReviewDecisionTraceModel.__tablename__
        == "review_decision_traces"
    )


def test_review_decision_trace_model_accepts_expected_fields():
    trace_id = uuid4()
    proposal_id = uuid4()
    created_at = datetime.now(timezone.utc)

    model = ReviewDecisionTraceModel(
        id=trace_id,
        proposal_id=proposal_id,
        decision="APPROVE",
        rationale="Proposal is valid.",
        reviewer="learning-review",
        created_at=created_at,
    )

    assert model.id == trace_id
    assert model.proposal_id == proposal_id
    assert model.decision == "APPROVE"
    assert model.rationale == "Proposal is valid."
    assert model.reviewer == "learning-review"
    assert model.created_at == created_at
