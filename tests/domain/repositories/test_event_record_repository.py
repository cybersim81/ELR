from app.domain.repositories.event_record_repository import EventRecordRepository


def test_event_record_repository_defines_required_contract():
    assert EventRecordRepository.__abstractmethods__ == {"save", "get"}
