from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.entities.audit_record import AuditRecord
from app.domain.repositories.audit_repository import AuditRepository
from app.persistence.models.audit_record_model import AuditRecordModel
from app.persistence.repositories.audit_repository import (
    SQLAlchemyAuditRepository,
)


def test_audit_repository_implements_domain_contract() -> None:
    repository = SQLAlchemyAuditRepository(Session())

    assert isinstance(repository, AuditRepository)


def test_audit_repository_record_adds_model() -> None:
    session = Session()
    repository = SQLAlchemyAuditRepository(session)

    audit = AuditRecord(
        entity_id=uuid4(),
        event_type="created",
        actor="test",
        metadata={"source": "test"},
    )

    repository.record(audit)

    model = next(iter(session.new))

    assert isinstance(model, AuditRecordModel)
    assert model.id == audit.id
    assert model.entity_id == audit.entity_id
    assert model.event_type == audit.event_type
    assert model.actor == audit.actor
    assert model.metadata == audit.metadata
    assert model.timestamp == audit.timestamp


def test_audit_repository_find_by_entity_returns_domain_records() -> None:
    session = Session()
    repository = SQLAlchemyAuditRepository(session)

    entity_id = uuid4()

    first = AuditRecord(
        entity_id=entity_id,
        event_type="created",
        actor="test",
        metadata={"sequence": 1},
    )
    second = AuditRecord(
        entity_id=entity_id,
        event_type="updated",
        actor="test",
        metadata={"sequence": 2},
    )

    session.add_all(
        [
            AuditRecordModel(
                id=first.id,
                entity_id=first.entity_id,
                event_type=first.event_type,
                actor=first.actor,
                metadata=first.metadata,
                timestamp=first.timestamp,
            ),
            AuditRecordModel(
                id=second.id,
                entity_id=second.entity_id,
                event_type=second.event_type,
                actor=second.actor,
                metadata=second.metadata,
                timestamp=second.timestamp,
            ),
        ]
    )

    result = repository.find_by_entity(entity_id)

    assert len(result) == 2
    assert all(isinstance(item, AuditRecord) for item in result)
    assert [item.id for item in result] == [first.id, second.id]
    assert [item.event_type for item in result] == ["created", "updated"]
