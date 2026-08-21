from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from uuid import UUID, uuid4


def _freeze(value):
    """
    Recursively convert mutable mapping/list/set values into immutable
    structures suitable for an immutable EventRecord.
    """

    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                key: _freeze(item)
                for key, item in value.items()
            }
        )

    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)

    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)

    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)

    return value


@dataclass(frozen=True)
class EventRecord:
    """
    Immutable transactional representation of an ELR event.

    This is an infrastructure/integration artifact.
    It is intentionally distinct from AuditRecord and from the
    knowledge domain model.
    """

    event_type: str
    event_source: str
    aggregate_type: str
    aggregate_id: UUID
    version: int
    payload: Mapping

    event_id: UUID = field(
        default_factory=uuid4
    )

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    published_at: datetime | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metadata: Mapping | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "payload",
            _freeze(self.payload),
        )

        if self.metadata is not None:
            object.__setattr__(
                self,
                "metadata",
                _freeze(self.metadata),
            )
