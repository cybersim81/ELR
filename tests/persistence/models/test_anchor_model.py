from datetime import datetime, timezone
from uuid import uuid4

from app.persistence.models.anchor_model import AnchorModel


def test_anchor_model_has_ipa():
    created_at = datetime.now(timezone.utc)

    anchor = AnchorModel(
        id=uuid4(),
        content="take a photo",
        type="phrase",
        ipa="/teɪk ə ˈfoʊtoʊ/",
        created_at=created_at,
    )

    assert anchor.ipa == "/teɪk ə ˈfoʊtoʊ/"
    assert anchor.created_at == created_at


def test_anchor_model_ipa_is_optional():
    created_at = datetime.now(timezone.utc)

    anchor = AnchorModel(
        id=uuid4(),
        content="take a photo",
        type="phrase",
        ipa=None,
        created_at=created_at,
    )

    assert anchor.ipa is None
    assert anchor.created_at == created_at
