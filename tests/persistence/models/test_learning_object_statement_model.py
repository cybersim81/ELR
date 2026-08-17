from app.persistence.models.learning_object_model import LearningObjectModel


def test_learning_object_model_knowledge_statement_mapping():
    columns = LearningObjectModel.__table__.columns

    assert columns["statement_text"].nullable is False
    assert columns["statement_language"].nullable is False

    model = LearningObjectModel(
        statement_text="A learning statement",
        statement_language="en",
    )

    assert model.statement_text == "A learning statement"
    assert model.statement_language == "en"
