from uuid import uuid4

from app.domain.repositories.event_record_repository import EventRecordRepository


def test_event_record_repository_is_abstract():
    assert EventRecordRepository.__abstractmethods__ == {"save", "get"}
