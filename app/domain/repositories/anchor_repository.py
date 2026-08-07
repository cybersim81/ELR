from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.anchor import Anchor


class AnchorRepository(ABC):

    @abstractmethod
    def save(
        self,
        anchor: Anchor
    ) -> None:
        pass


    @abstractmethod
    def get_by_id(
        self,
        anchor_id: UUID
    ) -> Anchor | None:
        pass