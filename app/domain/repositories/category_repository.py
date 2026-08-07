from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.knowledge_category import KnowledgeCategory


class CategoryRepository(ABC):

    @abstractmethod
    def save(
        self,
        category: KnowledgeCategory
    ) -> None:
        pass


    @abstractmethod
    def get_by_id(
        self,
        category_id: UUID
    ) -> KnowledgeCategory | None:
        pass


    @abstractmethod
    def get_all(
        self
    ) -> list[KnowledgeCategory]:
        pass