import pytest

from app.domain.entities.anchor import Anchor, InvalidAnchor


def test_anchor_can_be_created_without_ipa():
    anchor = Anchor(
        content="take a photo",
        type="phrase",
    )

    assert anchor.ipa is None


def test_anchor_can_be_created_with_ipa():
    anchor = Anchor(
        content="take a photo",
        type="phrase",
        ipa="/teɪk ə ˈfoʊtoʊ/",
    )

    assert anchor.ipa == "/teɪk ə ˈfoʊtoʊ/"


def test_anchor_rejects_empty_ipa():
    with pytest.raises(InvalidAnchor):
        Anchor(
            content="take a photo",
            type="phrase",
            ipa="",
        )


def test_anchor_rejects_whitespace_only_ipa():
    with pytest.raises(InvalidAnchor):
        Anchor(
            content="take a photo",
            type="phrase",
            ipa="   ",
        )


def test_ipa_does_not_change_anchor_identity():
    anchor_without_ipa = Anchor(
        content="take a photo",
        type="phrase",
    )

    anchor_with_ipa = Anchor(
        content="take a photo",
        type="phrase",
        ipa="/teɪk ə ˈfoʊtoʊ/",
    )

    assert anchor_without_ipa.id != anchor_with_ipa.id