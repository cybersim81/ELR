from app.persistence.models.anchor_model import AnchorModel
from app.persistence.models.base import Base
from app.persistence.models.learning_object_model import LearningObjectModel
from app.persistence.models.learning_object_value_models import (
    LearningObjectExampleModel,
    LearningObjectNoteModel,
)
from app.persistence.models.event_record_model import EventRecordModel


def test_persistence_models_are_registered_in_base_metadata():
    assert AnchorModel.__tablename__ in Base.metadata.tables
    assert LearningObjectModel.__tablename__ in Base.metadata.tables
    assert LearningObjectExampleModel.__tablename__ in Base.metadata.tables
    assert LearningObjectNoteModel.__tablename__ in Base.metadata.tables
    assert EventRecordModel.__tablename__ in Base.metadata.tables


def test_learning_object_owned_collections_use_delete_orphan():
    examples_relationship = LearningObjectModel.examples.property
    notes_relationship = LearningObjectModel.notes.property

    assert examples_relationship.cascade.delete_orphan
    assert notes_relationship.cascade.delete_orphan

def test_learning_object_owned_collections_are_collection_relationships():
    examples_relationship = LearningObjectModel.examples.property
    notes_relationship = LearningObjectModel.notes.property

    assert examples_relationship.uselist is True
    assert notes_relationship.uselist is True
