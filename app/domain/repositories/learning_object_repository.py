from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.learning_object import LearningObject


class LearningObjectRepository(ABC):
    """
    Repository contract for Learning Objects.
    """

    @abstractmethod
    def save(
        self,
        learning_object: LearningObject
    ) -> None:
        pass


    @abstractmethod
    def get_by_id(
        self,
        object_id: UUID
    ) -> LearningObject | None:
        pass
