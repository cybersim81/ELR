from dataclasses import dataclass, field
from uuid import UUID, uuid4


class InvalidCategory(Exception):
    pass


@dataclass
class KnowledgeCategory:
    """
    Taxonomy node.
    """

    name: str

    parent_id: UUID | None = None

    id: UUID = field(
        default_factory=uuid4
    )

    def __post_init__(self):

        if not self.name.strip():
            raise InvalidCategory(
                "Category name cannot be empty"
            )