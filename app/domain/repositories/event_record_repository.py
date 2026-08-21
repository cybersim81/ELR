from abc import ABC, abstractmethod
from uuid import UUID

from app.events.event_record import EventRecord


class EventRecordRepository(ABC):

    @abstractmethod
    def save(self, event: EventRecord) -> None:
        ...

    @abstractmethod
    def get(self, event_id: UUID) -> EventRecord | None:
        ...
