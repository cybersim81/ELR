from app.domain.entities.review_decision import ReviewDecision


def test_review_decision_contains_all_authorized_decisions():
    assert set(ReviewDecision) == {
        ReviewDecision.APPROVE,
        ReviewDecision.REJECT,
        ReviewDecision.REQUEST_REVISION,
    }


def test_review_decision_values_match_normative_semantics():
    assert ReviewDecision.APPROVE.value == "APPROVE"
    assert ReviewDecision.REJECT.value == "REJECT"
    assert ReviewDecision.REQUEST_REVISION.value == "REQUEST_REVISION"


def test_review_decision_is_string_compatible():
    assert ReviewDecision.APPROVE == "APPROVE"
    assert ReviewDecision.REJECT == "REJECT"
    assert ReviewDecision.REQUEST_REVISION == "REQUEST_REVISION"
