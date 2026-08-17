from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base


class VersionModel(Base):
    """SQLAlchemy persistence model for the Version domain entity."""

    __tablename__ = "versions"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    learning_object_id: Mapped[UUID] = mapped_column(
        ForeignKey("learning_objects.id"),
        nullable=False,
    )

    number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
