from uuid import uuid4

from app.application.services.audit_service import AuditService
from app.domain.entities.audit_record import AuditRecord


class SpyAuditRepository:
    """Test double for the AuditRepository application boundary."""

    def __init__(self) -> None:
        self.recorded: list[AuditRecord] = []
        self.requested_entity_ids = []

    def record(
        self,
        audit: AuditRecord,
    ) -> None:
        self.recorded.append(audit)

    def find_by_entity(
        self,
        entity_id,
    ) -> list[AuditRecord]:
        self.requested_entity_ids.append(entity_id)

        return [
            audit
            for audit in self.recorded
            if audit.entity_id == entity_id
        ]


def test_record_event_coordinates_audit_creation_and_delegates_persistence():
    repository = SpyAuditRepository()
    service = AuditService(repository)

    entity_id = uuid4()

    audit = service.record_event(
        entity_id=entity_id,
        event_type="LearningObjectApproved",
        actor="reviewer",
        metadata={
            "version": 1,
        },
    )

    assert isinstance(audit, AuditRecord)

    assert audit.entity_id == entity_id
    assert audit.event_type == "LearningObjectApproved"
    assert audit.actor == "reviewer"
    assert audit.metadata == {
        "version": 1,
    }

    assert repository.recorded == [audit]


def test_get_events_coordinates_retrieval_through_audit_repository():
    repository = SpyAuditRepository()
    service = AuditService(repository)

    entity_id = uuid4()

    expected = AuditRecord(
        entity_id=entity_id,
        event_type="LearningObjectCreated",
        actor="producer",
    )

    repository.record(expected)

    result = service.get_events(entity_id)

    assert result == [expected]
    assert repository.requested_entity_ids == [entity_id]


def test_record_event_preserves_audit_record_semantics_without_redefining_them():
    repository = SpyAuditRepository()
    service = AuditService(repository)

    entity_id = uuid4()

    audit = service.record_event(
        entity_id=entity_id,
        event_type="LearningObjectUpdated",
        actor="reviewer",
        metadata={
            "version": 2,
            "reason": "knowledge update",
        },
    )

    persisted = repository.recorded[0]

    assert persisted is audit
    assert persisted.entity_id == entity_id
    assert persisted.event_type == "LearningObjectUpdated"
    assert persisted.actor == "reviewer"
    assert persisted.metadata == {
        "version": 2,
        "reason": "knowledge update",
    }


def test_get_events_does_not_bypass_audit_repository():
    repository = SpyAuditRepository()
    service = AuditService(repository)

    entity_id = uuid4()

    result = service.get_events(entity_id)

    assert result == []
    assert repository.requested_entity_ids == [entity_id]
