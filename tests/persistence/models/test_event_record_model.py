from app.persistence.models.event_record_model import EventRecordModel


def test_event_record_model_metadata():
    assert EventRecordModel.__tablename__ == "event_records"

    columns = EventRecordModel.__table__.columns

    assert columns["event_id"].primary_key is True

    assert columns["event_type"].nullable is False
    assert columns["event_source"].nullable is False
    assert columns["aggregate_type"].nullable is False
    assert columns["aggregate_id"].nullable is False
    assert columns["version"].nullable is False
    assert columns["payload"].nullable is False
    assert columns["occurred_at"].nullable is False
    assert columns["published_at"].nullable is True
    assert columns["created_at"].nullable is False
    assert columns["metadata"].nullable is True


def test_event_record_model_uses_jsonb_for_payload_and_metadata():
    columns = EventRecordModel.__table__.columns

    assert columns["payload"].type.__class__.__name__ == "JSONB"
    assert columns["metadata"].type.__class__.__name__ == "JSONB"
