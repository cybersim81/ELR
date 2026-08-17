from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base


class AuditRecordModel(Base):
    """SQLAlchemy persistence model for the AuditRecord domain entity."""

    __tablename__ = "audit_records"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    entity_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    actor: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    metadata_: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
