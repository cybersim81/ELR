from uuid import uuid4

from app.persistence.models.anchor_model import AnchorModel


def test_anchor_model_has_ipa():
    anchor = AnchorModel(
        id=uuid4(),
        content="take a photo",
        type="phrase",
        ipa="/teɪk ə ˈfoʊtoʊ/",
        created_at=None,
    )

    assert anchor.ipa == "/teɪk ə ˈfoʊtoʊ/"


def test_anchor_model_ipa_is_optional():
    anchor = AnchorModel(
        id=uuid4(),
        content="take a photo",
        type="phrase",
        ipa=None,
        created_at=None,
    )

    assert anchor.ipa is None
