from dataclasses import dataclass


@dataclass(frozen=True)
class Note:
    """
    Note associated with a Learning Object.

    This is a Value Object of the Domain Model.
    It has no autonomous domain or persistence identity.
    """

    content: str

    def __post_init__(self):
        if not self.content.strip():
            raise ValueError(
                "Note content cannot be empty"
            )