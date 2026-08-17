from app.persistence.models.learning_object_model import LearningObjectModel


def test_learning_object_model_foreign_keys():
    columns = LearningObjectModel.__table__.columns

    anchor_fks = columns["anchor_id"].foreign_keys
    category_fks = columns["category_id"].foreign_keys

    assert len(anchor_fks) == 1
    assert next(iter(anchor_fks)).target_fullname == "anchors.id"

    assert len(category_fks) == 1
    assert next(iter(category_fks)).target_fullname == "categories.id"


def test_learning_object_model_owned_value_relationships():
    relationships = LearningObjectModel.__mapper__.relationships

    assert "examples" in relationships
    assert "notes" in relationships

    assert relationships["examples"].cascade.delete_orphan
    assert relationships["notes"].cascade.delete_orphan
