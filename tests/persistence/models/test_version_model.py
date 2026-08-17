from app.persistence.models.version_model import VersionModel


def test_version_model_metadata():
    assert VersionModel.__tablename__ == "versions"

    columns = VersionModel.__table__.columns

    assert columns["id"].primary_key is True
    assert columns["learning_object_id"].nullable is False
    assert columns["number"].nullable is False
    assert columns["snapshot"].nullable is False
    assert columns["created_at"].nullable is False

    foreign_keys = columns["learning_object_id"].foreign_keys

    assert len(foreign_keys) == 1
    assert next(iter(foreign_keys)).target_fullname == "learning_objects.id"
