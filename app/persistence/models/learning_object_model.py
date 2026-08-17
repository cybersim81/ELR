from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class LearningObjectModel(Base):
    __tablename__ = "learning_objects"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    anchor_id: Mapped[UUID] = mapped_column(
        ForeignKey("anchors.id"),
        nullable=False,
    )

    statement_text: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    statement_language: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    category_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        Enum(
            "Candidate",
            "Proposed",
            "Active",
            "Retired",
            name="learning_object_state",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )