from uuid import uuid4

import pytest

from app.application.errors import UnauthorizedOperation
from app.application.security.authorization import AuthorizationService
from app.application.security.identity import IdentityContext
from app.application.security.permissions import Permission
from app.application.security.roles import Role


def make_identity(*roles: Role) -> IdentityContext:
    return IdentityContext(
        actor_id=uuid4(),
        actor_type="Human Reviewer",
        roles=frozenset(role.value for role in roles),
    )


def test_knowledge_reviewer_can_approve_knowledge() -> None:
    identity = make_identity(Role.KNOWLEDGE_REVIEWER)

    AuthorizationService().require(
        identity,
        Permission.APPROVE_KNOWLEDGE,
    )


def test_knowledge_producer_can_create_candidate() -> None:
    identity = make_identity(Role.KNOWLEDGE_PRODUCER)

    AuthorizationService().require(
        identity,
        Permission.CREATE_CANDIDATE,
    )


def test_read_only_user_can_read_knowledge() -> None:
    identity = make_identity(Role.READ_ONLY_USER)

    AuthorizationService().require(
        identity,
        Permission.READ_KNOWLEDGE,
    )


def test_read_only_user_cannot_approve_knowledge() -> None:
    identity = make_identity(Role.READ_ONLY_USER)

    with pytest.raises(UnauthorizedOperation):
        AuthorizationService().require(
            identity,
            Permission.APPROVE_KNOWLEDGE,
        )


def test_unknown_role_has_no_permissions() -> None:
    identity = IdentityContext(
        actor_id=uuid4(),
        actor_type="Unknown",
        roles=frozenset({"UNKNOWN_ROLE"}),
    )

    with pytest.raises(UnauthorizedOperation):
        AuthorizationService().require(
            identity,
            Permission.READ_KNOWLEDGE,
        )
