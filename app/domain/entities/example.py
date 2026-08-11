from dataclasses import dataclass


@dataclass(frozen=True)
class Example:
    """
    Example associated with a Learning Object.

    This is a Value Object of the Domain Model.
    It has no autonomous domain or persistence identity.
    """

    content: str

    def __post_init__(self):
        if not self.content.strip():
            raise ValueError(
                "Example content cannot be empty"
            )