from uuid import uuid4

from app.domain.entities.learning_object import (
    LearningObject,
    LearningObjectState,
    InvalidStateTransition,
)


def create_object():

    return LearningObject(
        anchor_id=uuid4(),
        statement="Example knowledge statement",
        category_id=uuid4(),
    )


def test_initial_state():

    obj = create_object()

    assert obj.state == LearningObjectState.CANDIDATE


def test_submit_for_review():

    obj = create_object()

    obj.submit_for_review()

    assert obj.state == LearningObjectState.PROPOSED


def test_invalid_transition():

    obj = create_object()

    try:
        obj.approve()

        assert False

    except InvalidStateTransition:
        assert True


def test_full_approval_flow():

    obj = create_object()

    obj.submit_for_review()
    obj.mark_reviewed()
    obj.approve()

    assert obj.state == LearningObjectState.ACTIVE
