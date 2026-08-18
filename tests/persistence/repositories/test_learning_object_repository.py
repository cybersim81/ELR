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

def test_learning_object_repository_save_updates_existing_learning_object(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )

    import importlib

    import app.persistence.database as database

    database = importlib.reload(database)

    from app.persistence.models.anchor_model import AnchorModel
    from app.persistence.models.audit_record_model import AuditRecordModel
    from app.persistence.models.base import Base
    from app.persistence.models.knowledge_category_model import (
        KnowledgeCategoryModel,
    )
    from app.persistence.models.learning_object_model import (
        LearningObjectModel,
    )
    from app.persistence.models.learning_object_value_models import (
        LearningObjectExampleModel,
        LearningObjectNoteModel,
    )
    from app.persistence.models.version_model import VersionModel

    Base.metadata.create_all(database.engine)

    session = database.SessionFactory()
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

    session.flush()

    persisted = repository.get_by_id(learning_object.id)

    assert persisted is not None
    assert persisted.state.value == learning_object.state.value

    persisted.state = type(persisted.state).Proposed

    repository.save(persisted)

    session.flush()
    session.expire_all()

    updated = repository.get_by_id(learning_object.id)

    assert updated is not None
    assert updated.state.value == "Proposed"

    session.close()
