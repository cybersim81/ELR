from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from app.events.event_record import EventRecord
from app.persistence.models.event_record_model import EventRecordModel
from app.persistence.repositories.event_record_repository import (
    SQLAlchemyEventRecordRepository,
)


def make_event() -> EventRecord:
    return EventRecord(
        event_type="LearningObjectCreated",
        event_source="learning_object_service",
        aggregate_type="LearningObject",
        aggregate_id=uuid4(),
        version=1,
        payload={
            "title": "Test object",
            "status": "candidate",
        },
        occurred_at=datetime.now(timezone.utc),
        metadata={
            "actor": "test",
        },
    )


def test_save_maps_event_record_to_persistence_model():
    session = Mock()
    repository = SQLAlchemyEventRecordRepository(session)

    event = make_event()

    repository.save(event)

    session.add.assert_called_once()

    model = session.add.call_args.args[0]

    assert isinstance(model, EventRecordModel)
    assert model.event_id == event.event_id
    assert model.event_type == event.event_type
    assert model.event_source == event.event_source
    assert model.aggregate_type == event.aggregate_type
    assert model.aggregate_id == event.aggregate_id
    assert model.version == event.version
    assert model.payload == dict(event.payload)
    assert model.occurred_at == event.occurred_at
    assert model.published_at == event.published_at
    assert model.created_at == event.created_at
    assert model.metadata_ == dict(event.metadata)


def test_save_does_not_commit():
    session = Mock()
    repository = SQLAlchemyEventRecordRepository(session)

    repository.save(make_event())

    session.commit.assert_not_called()
    session.flush.assert_not_called()


def test_get_returns_event_record():
    session = Mock()
    repository = SQLAlchemyEventRecordRepository(session)

    event = make_event()

    model = EventRecordModel(
        event_id=event.event_id,
        event_type=event.event_type,
        event_source=event.event_source,
        aggregate_type=event.aggregate_type,
        aggregate_id=event.aggregate_id,
        version=event.version,
        payload=dict(event.payload),
        occurred_at=event.occurred_at,
        published_at=event.published_at,
        created_at=event.created_at,
        metadata_=dict(event.metadata),
    )

    session.scalar.return_value = model

    restored = repository.get(event.event_id)

    assert restored is not None
    assert restored.event_id == event.event_id
    assert restored.event_type == event.event_type
    assert restored.event_source == event.event_source
    assert restored.aggregate_type == event.aggregate_type
    assert restored.aggregate_id == event.aggregate_id
    assert restored.version == event.version
    assert restored.payload == event.payload
    assert restored.occurred_at == event.occurred_at
    assert restored.published_at == event.published_at
    assert restored.created_at == event.created_at
    assert restored.metadata == event.metadata


def test_get_returns_none_when_event_record_does_not_exist():
    session = Mock()
    repository = SQLAlchemyEventRecordRepository(session)

    session.scalar.return_value = None

    result = repository.get(uuid4())

    assert result is None
