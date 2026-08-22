from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base


class EventRecordModel(Base):
    """SQLAlchemy persistence model for the transactional Event Record."""

    __tablename__ = "event_records"

    event_id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )

    event_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    event_source: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    aggregate_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    aggregate_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )