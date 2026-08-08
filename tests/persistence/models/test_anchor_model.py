from datetime import datetime
from uuid import uuid4

from sqlalchemy import inspect

from app.persistence.models.anchor_model import AnchorModel


def test_anchor_model_mapping():
    mapper = inspect(AnchorModel)

    assert AnchorModel.__tablename__ == "anchors"

    columns = mapper.columns

    assert columns["id"].primary_key is True
    assert columns["content"].nullable is False
    assert columns["type"].nullable is False
    assert columns["created_at"].nullable is False


def test_anchor_model_can_be_instantiated():
    anchor = AnchorModel(
        id=uuid4(),
        content="Test anchor",
        type="source",
        created_at=datetime.now(),
    )

    assert anchor.content == "Test anchor"
    assert anchor.type == "source"