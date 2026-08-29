from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class IdentityContext:
    """
    Authenticated identity propagated through the ELR application boundary.

    The context contains only identity and effective role information.
    Authentication itself remains delegated to an external provider.
    """

    actor_id: UUID
    actor_type: str
    roles: frozenset[str]

    def has_role(self, role: str) -> bool:
        return role in self.roles
