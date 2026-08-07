from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.audit_record import AuditRecord


class AuditRepository(ABC):

    @abstractmethod
    def record(
        self,
        audit: AuditRecord
    ) -> None:
        pass


    @abstractmethod
    def find_by_entity(
        self,
        entity_id: UUID
    ) -> list[AuditRecord]:
        pass