from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.events.event_record import EventRecord


def make_event() -> EventRecord:
    return EventRecord(
        event_type="LearningObjectCreated",
        event_source="learning_object_service",
        aggregate_type="LearningObject",
        aggregate_id=uuid4(),
        version=1,
        payload={
            "statement": "Use take + photo",
            "nested": {
                "source": "test",
            },
            "items": [
                "take",
                "photo",
            ],
        },
        metadata={
            "origin": "test",
        },
    )


def test_event_record_contains_required_fields():
    event = make_event()

    assert isinstance(event.event_id, UUID)
    assert event.event_type == "LearningObjectCreated"
    assert event.event_source == "learning_object_service"
    assert event.aggregate_type == "LearningObject"
    assert isinstance(event.aggregate_id, UUID)
    assert event.version == 1

    assert event.payload["statement"] == "Use take + photo"
    assert event.metadata["origin"] == "test"

    assert isinstance(event.occurred_at, datetime)
    assert isinstance(event.created_at, datetime)
    assert event.occurred_at.tzinfo is not None
    assert event.created_at.tzinfo is not None

    assert event.published_at is None


def test_event_record_is_immutable():
    event = make_event()

    with pytest.raises(AttributeError):
        event.event_type = "Changed"


def test_event_record_payload_is_immutable():
    event = make_event()

    with pytest.raises(TypeError):
        event.payload["statement"] = "Changed"


def test_event_record_nested_payload_is_immutable():
    event = make_event()

    with pytest.raises(TypeError):
        event.payload["nested"]["source"] = "Changed"


def test_event_record_payload_list_is_immutable():
    event = make_event()

    with pytest.raises(TypeError):
        event.payload["items"][0] = "Changed"


def test_event_record_defensively_copies_payload():
    payload = {
        "statement": "Original",
    }

    event = EventRecord(
        event_type="LearningObjectCreated",
        event_source="learning_object_service",
        aggregate_type="LearningObject",
        aggregate_id=uuid4(),
        version=1,
        payload=payload,
    )

    payload["statement"] = "Changed"

    assert event.payload["statement"] == "Original"


def test_event_record_defensively_copies_metadata():
    metadata = {
        "origin": "Original",
    }

    event = EventRecord(
        event_type="LearningObjectCreated",
        event_source="learning_object_service",
        aggregate_type="LearningObject",
        aggregate_id=uuid4(),
        version=1,
        payload={},
        metadata=metadata,
    )

    metadata["origin"] = "Changed"

    assert event.metadata["origin"] == "Original"
