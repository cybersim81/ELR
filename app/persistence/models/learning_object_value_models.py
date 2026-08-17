from datetime import datetime, timezone
from uuid import uuid4

from app.persistence.models.learning_object_model import LearningObjectModel


def test_learning_object_model_constructs_with_required_fields():
    anchor_id = uuid4()
    category_id = uuid4()
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)

    model = LearningObjectModel(
        id=uuid4(),
        anchor_id=anchor_id,
        statement_text="A learning statement",
        statement_language="en",
        category_id=category_id,
        state="Candidate",
        created_at=created_at,
        updated_at=updated_at,
    )

    assert model.anchor_id == anchor_id
    assert model.statement_text == "A learning statement"
    assert model.statement_language == "en"
    assert model.category_id == category_id
    assert model.state == "Candidate"
    assert model.created_at == created_at
    assert model.updated_at == updated_at
