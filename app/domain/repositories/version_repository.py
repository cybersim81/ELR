from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.version import Version


class VersionRepository(ABC):

    @abstractmethod
    def save(
        self,
        version: Version
    ) -> None:
        pass


    @abstractmethod
    def get_history(
        self,
        entity_id: UUID
    ) -> list[Version]:
        pass