from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.audit_record import AuditRecord
from app.domain.repositories.audit_repository import AuditRepository
from app.persistence.models.audit_record_model import AuditRecordModel


class SQLAlchemyAuditRepository(AuditRepository):
    """
    SQLAlchemy implementation of the Audit repository.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, audit: AuditRecord) -> None:
        model = AuditRecordModel(
            id=audit.id,
            entity_id=audit.entity_id,
            event_type=audit.event_type,
            actor=audit.actor,
            metadata_=audit.metadata,
            timestamp=audit.timestamp,
        )

        self._session.add(model)

    def find_by_entity(self, entity_id: UUID) -> list[AuditRecord]:
        models = (
            self._session.query(AuditRecordModel)
            .filter(AuditRecordModel.entity_id == entity_id)
            .order_by(AuditRecordModel.timestamp.asc())
            .all()
        )

        return [
            AuditRecord(
                id=model.id,
                entity_id=model.entity_id,
                event_type=model.event_type,
                actor=model.actor,
                metadata=model.metadata_,
                timestamp=model.timestamp,
            )
            for model in models
        ]
