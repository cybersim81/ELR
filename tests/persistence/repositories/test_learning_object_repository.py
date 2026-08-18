from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.entities.knowledge_statement import KnowledgeStatement
from app.domain.entities.learning_object import LearningObject
from app.domain.repositories.learning_object_repository import (
    LearningObjectRepository,
)
from app.persistence.repositories.learning_object_repository import (
    SQLAlchemyLearningObjectRepository,
)


def test_learning_object_repository_implements_domain_contract() -> None:
    repository = SQLAlchemyLearningObjectRepository(Session())

    assert isinstance(repository, LearningObjectRepository)


def test_learning_object_repository_save_adds_learning_object_model() -> None:
    session = Session()
    repository = SQLAlchemyLearningObjectRepository(session)

    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=KnowledgeStatement(
            text="Test knowledge statement",
            language="en",
        ),
        category_id=uuid4(),
    )

    repository.save(learning_object)

    model = session.new.pop()

    assert model.id == learning_object.id
    assert model.anchor_id == learning_object.anchor_id
    assert model.statement_text == learning_object.statement.text
    assert model.statement_language == learning_object.statement.language
    assert model.category_id == learning_object.category_id
    assert model.state == learning_object.state.value
    assert model.created_at == learning_object.created_at
    assert model.updated_at == learning_object.updated_at

def test_learning_object_repository_save_updates_existing_learning_object() -> None:
    session = Session()
    repository = SQLAlchemyLearningObjectRepository(session)

    learning_object = LearningObject(
        anchor_id=uuid4(),
        statement=KnowledgeStatement(
            text="Test knowledge statement",
            language="en",
        ),
        category_id=uuid4(),
    )

    repository.save(learning_object)

    model = session.new.pop()

    assert model.id == learning_object.id

    model.state = "Proposed"

    session.add(model)

    session.flush()

    assert model.id == learning_object.id
    assert model.state == "Proposed"
