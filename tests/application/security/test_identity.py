from uuid import uuid4

from app.application.security.identity import IdentityContext


def test_identity_context_is_immutable() -> None:
    identity = IdentityContext(
        actor_id=uuid4(),
        actor_type="User",
        roles=frozenset({"READ_ONLY_USER"}),
    )

    assert identity.actor_type == "User"
    assert identity.has_role("READ_ONLY_USER")
    assert not identity.has_role("KNOWLEDGE_REVIEWER")
