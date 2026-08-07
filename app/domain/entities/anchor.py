from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


class InvalidAnchor(Exception):
    pass


@dataclass(frozen=True)
class Anchor:
    """
    Linguistic reference point for ELR knowledge.
    """

    content: str
    type: str

    id: UUID = field(default_factory=uuid4)

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        if not self.content.strip():
            raise InvalidAnchor(
                "Anchor content cannot be empty"
            )