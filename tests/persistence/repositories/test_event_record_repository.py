from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.events.event_record import EventRecord
from app.persistence.models.base import Base
from app.persistence.repositories.event_record_repository import (
    SQLAlchemyEventRecordRepository,
)


def test_save_and_get_event_record():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)

    event = EventRecord(
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

    with Session() as session:
        repository = SQLAlchemyEventRecordRepository(session)

        repository.save(event)
        session.commit()

    with Session() as session:
        repository = SQLAlchemyEventRecordRepository(session)

        restored = repository.get(event.event_id)

    assert restored is not None
    assert restored.event_id == event.event_id
    assert restored.event_type == event.event_type
    assert restored.event_source == event.event_source
    assert restored.aggregate_type == event.aggregate_type
    assert restored.aggregate_id == event.aggregate_id
    assert restored.version == event.version
    assert restored.payload == event.payload
    assert restored.metadata == event.metadata
    assert restored.occurred_at == event.occurred_at
    assert restored.published_at is None
    assert restored.created_at == event.created_at
