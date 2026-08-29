from app.application.errors import UnauthorizedOperation
from app.application.security.identity import IdentityContext
from app.application.security.permissions import Permission
from app.application.security.roles import Role


_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.SYSTEM_ADMIN: frozenset(
        {
            Permission.CONFIGURE_SYSTEM,
            Permission.MANAGE_TECHNICAL,
        }
    ),
    Role.KNOWLEDGE_REVIEWER: frozenset(
        {
            Permission.REVIEW_KNOWLEDGE,
            Permission.APPROVE_KNOWLEDGE,
            Permission.REJECT_KNOWLEDGE,
        }
    ),
    Role.KNOWLEDGE_PRODUCER: frozenset(
        {
            Permission.CREATE_CANDIDATE,
            Permission.PROPOSE_CHANGE,
        }
    ),
    Role.READ_ONLY_USER: frozenset(
        {
            Permission.READ_KNOWLEDGE,
        }
    ),
}


class AuthorizationService:
    """
    Deterministic authorization boundary for ELR application operations.

    Role-to-permission mapping is centralized here and is derived from
    the ELR Security Implementation Specification.
    """

    def is_allowed(
        self,
        identity: IdentityContext,
        permission: Permission,
    ) -> bool:
        for role_name in identity.roles:
            try:
                role = Role(role_name)
            except ValueError:
                continue

            if permission in _ROLE_PERMISSIONS.get(
                role,
                frozenset(),
            ):
                return True

        return False

    def require(
        self,
        identity: IdentityContext,
        permission: Permission,
    ) -> None:
        if not self.is_allowed(
            identity,
            permission,
        ):
            raise UnauthorizedOperation(
                f"Identity is not authorized for "
                f"{permission.value}."
            )
