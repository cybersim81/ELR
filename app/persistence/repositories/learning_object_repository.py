from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.learning_object import LearningObject
from app.domain.repositories.learning_object_repository import LearningObjectRepository
from app.persistence.models.learning_object_model import LearningObjectModel

class SQLAlchemyLearningObjectRepository(LearningObjectRepository):
    """
    SQLAlchemy implementation of the LearningObject repository.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, learning_object: LearningObject) -> None:
        model = LearningObjectModel(
            id=learning_object.id,
            anchor_id=learning_object.anchor_id,
            statement_text=learning_object.statement.text,
            statement_language=learning_object.statement.language,
            category_id=learning_object.category_id,
            state=learning_object.state.value,
            created_at=learning_object.created_at,
            updated_at=learning_object.updated_at,
        )

        self._session.add(model)

    def get_by_id(self, object_id: UUID) -> LearningObject | None:
        model = self._session.get(LearningObjectModel, object_id)

        if model is None:
            return None

        raise NotImplementedError(
            "LearningObject persistence-to-domain mapping is not implemented yet"
        )
