from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.repositories.event_record_repository import EventRecordRepository
from app.events.event_record import EventRecord
from app.persistence.models.event_record_model import EventRecordModel


class SQLAlchemyEventRecordRepository(EventRecordRepository):
    """
    SQLAlchemy implementation of the Event Record repository.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, event: EventRecord) -> None:
        model = EventRecordModel(
            event_id=event.event_id,
            event_type=event.event_type,
            event_source=event.event_source,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            version=event.version,
            payload=dict(event.payload),
            occurred_at=event.occurred_at,
            published_at=event.published_at,
            created_at=event.created_at,
            metadata_=(
                dict(event.metadata)
                if event.metadata is not None
                else None
            ),
        )

        self._session.add(model)

    def get(self, event_id: UUID) -> EventRecord | None:
        model = self._session.scalar(
            select(EventRecordModel).where(
                EventRecordModel.event_id == event_id
            )
        )

        if model is None:
            return None

        return EventRecord(
            event_id=model.event_id,
            event_type=model.event_type,
            event_source=model.event_source,
            aggregate_type=model.aggregate_type,
            aggregate_id=model.aggregate_id,
            version=model.version,
            payload=model.payload,
            occurred_at=model.occurred_at,
            published_at=model.published_at,
            created_at=model.created_at,
            metadata=model.metadata_,
        )
