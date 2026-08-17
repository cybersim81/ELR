from app.persistence.models.anchor_model import AnchorModel
from app.persistence.models.base import Base
from app.persistence.models.learning_object_model import LearningObjectModel
from app.persistence.models.learning_object_value_models import (
    LearningObjectExampleModel,
    LearningObjectNoteModel,
)


def test_persistence_models_are_registered_in_base_metadata():
    assert AnchorModel.__tablename__ in Base.metadata.tables
    assert LearningObjectModel.__tablename__ in Base.metadata.tables
    assert LearningObjectExampleModel.__tablename__ in Base.metadata.tables
    assert LearningObjectNoteModel.__tablename__ in Base.metadata.tables
