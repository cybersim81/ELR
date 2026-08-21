from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EventRecord:
    """
    Immutable transactional representation of an ELR event.

    This is an infrastructure/integration artifact.
    It is intentionally distinct from AuditRecord and from
    the knowledge domain model.
    """

    event_type: str
    event_source: str
    aggregate_type: str
    aggregate_id: UUID
    version: int
    payload: dict

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

    metadata: dict | None = None
