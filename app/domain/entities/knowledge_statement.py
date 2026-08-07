from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


class InvalidKnowledgeStatement(Exception):
    pass


@dataclass(frozen=True)
class KnowledgeStatement:
    """
    Cognitive content associated with a Learning Object.
    """

    text: str
    language: str

    id: UUID = field(default_factory=uuid4)

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):

        if not self.text.strip():
            raise InvalidKnowledgeStatement(
                "Statement text cannot be empty"
            )