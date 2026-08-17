from uuid import uuid4

from app.domain.entities.knowledge_statement import KnowledgeStatement
from app.domain.entities.learning_object import (
    InvalidStateTransition,
    LearningObject,
    LearningObjectState,
)


def create_object():
    return LearningObject(
        anchor_id=uuid4(),
        statement=KnowledgeStatement(
            text="Example knowledge statement",
            language="en",
        ),
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
    obj.approve()

    assert obj.state == LearningObjectState.ACTIVE


def test_retire_active_object():
    obj = create_object()

    obj.submit_for_review()
    obj.approve()
    obj.retire()

    assert obj.state == LearningObjectState.RETIRED


def test_update_knowledge_keeps_active_state():
    obj = create_object()

    obj.submit_for_review()
    obj.approve()

    obj.update_knowledge(
        KnowledgeStatement(
            text="Updated knowledge statement",
            language="en",
        )
    )

    assert obj.state == LearningObjectState.ACTIVE
    assert obj.statement.text == "Updated knowledge statement"
    assert obj.statement.language == "en"


def test_knowledge_statement_is_part_of_learning_object():
    statement = KnowledgeStatement(
        text="Example knowledge statement",
        language="en",
    )

    obj = LearningObject(
        anchor_id=uuid4(),
        statement=statement,
        category_id=uuid4(),
    )

    assert obj.statement is statement


def test_knowledge_statement_has_no_independent_identity():
    statement = KnowledgeStatement(
        text="Example knowledge statement",
        language="en",
    )

    assert not hasattr(statement, "id")
    assert not hasattr(statement, "created_at")

def test_candidate_cannot_be_retired():
    obj = create_object()

    try:
        obj.retire()
        assert False
    except InvalidStateTransition:
        assert True


def test_proposed_cannot_be_retired():
    obj = create_object()

    obj.submit_for_review()

    try:
        obj.retire()
        assert False
    except InvalidStateTransition:
        assert True


def test_active_cannot_be_submitted_for_review_again():
    obj = create_object()

    obj.submit_for_review()
    obj.approve()

    try:
        obj.submit_for_review()
        assert False
    except InvalidStateTransition:
        assert True


def test_proposed_cannot_be_updated():
    obj = create_object()

    obj.submit_for_review()

    try:
        obj.update_knowledge(
            KnowledgeStatement(
                text="Updated knowledge statement",
                language="en",
            )
        )
        assert False
    except InvalidStateTransition:
        assert True


def test_retired_cannot_be_reactivated():
    obj = create_object()

    obj.submit_for_review()
    obj.approve()
    obj.retire()

    try:
        obj.approve()
        assert False
    except InvalidStateTransition:
        assert True


def test_retired_cannot_be_submitted_for_review():
    obj = create_object()

    obj.submit_for_review()
    obj.approve()
    obj.retire()

    try:
        obj.submit_for_review()
        assert False
    except InvalidStateTransition:
        assert True


def test_retired_cannot_be_updated():
    obj = create_object()

    obj.submit_for_review()
    obj.approve()
    obj.retire()

    try:
        obj.update_knowledge(
            KnowledgeStatement(
                text="Updated knowledge statement",
                language="en",
            )
        )
        assert False
    except InvalidStateTransition:
        assert True
