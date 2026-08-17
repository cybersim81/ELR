from app.persistence.models.knowledge_category_model import KnowledgeCategoryModel


def test_knowledge_category_model_metadata():
    assert KnowledgeCategoryModel.__tablename__ == "categories"

    columns = KnowledgeCategoryModel.__table__.columns

    assert columns["id"].primary_key is True
    assert columns["name"].nullable is False
    assert columns["parent_id"].nullable is True

    foreign_keys = columns["parent_id"].foreign_keys

    assert len(foreign_keys) == 1
    assert next(iter(foreign_keys)).target_fullname == "categories.id"
