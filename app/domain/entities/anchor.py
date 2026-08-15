from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class InvalidAnchor(Exception):
    pass


@dataclass(frozen=True)
class Anchor:
    """
    Linguistic reference point for ELR knowledge.
    """

    content: str
    type: str
    ipa: str | None = None
    id: UUID = field(default_factory=uuid4)

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("ipa")
    @classmethod
    def validate_ipa(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Anchor IPA cannot be empty")
        return value

    def __post_init__(self):
        if not self.content.strip():
            raise InvalidAnchor(
                "Anchor content cannot be empty"
            )
