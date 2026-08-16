from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Version:
    """
    Immutable historical snapshot of a LearningObject.
    """

    learning_object_id: UUID
    number: int
    snapshot: dict

    id: UUID = field(
        default_factory=uuid4
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
