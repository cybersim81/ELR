from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base


class AnchorModel(Base):
    """SQLAlchemy persistence model for the Anchor domain entity."""

    __tablename__ = "anchors"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    content: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    ipa: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
