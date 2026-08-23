from uuid import UUID

from app.domain.entities.audit_record import AuditRecord
from app.domain.repositories.audit_repository import AuditRepository

class AuditService:
"""Application boundary for audit record coordination."""

def __init__(
    self,
    audit_repository: AuditRepository,
) -> None:
    self._audit_repository = audit_repository

def record_event(
    self,
    entity_id: UUID,
    event_type: str,
    actor: str,
    metadata: dict | None = None,
) -> AuditRecord:
    """Record an application-level audit event."""
    audit = AuditRecord(
        entity_id=entity_id,
        event_type=event_type,
        actor=actor,
        metadata=metadata or {},
    )

    self._audit_repository.record(audit)

    return audit

def get_events(
    self,
    entity_id: UUID,
) -> list[AuditRecord]:
    """Return audit history for an entity."""
    return self._audit_repository.find_by_entity(
        entity_id
    )
