from app.persistence.models.audit_record_model import AuditRecordModel


def test_audit_record_model_metadata():
    assert AuditRecordModel.__tablename__ == "audit_records"

    columns = AuditRecordModel.__table__.columns

    assert columns["id"].primary_key is True
    assert columns["entity_id"].nullable is False
    assert columns["event_type"].nullable is False
    assert columns["actor"].nullable is False
    assert columns["timestamp"].nullable is False
    assert columns["metadata"].nullable is False

    assert columns["entity_id"].foreign_keys == set()
