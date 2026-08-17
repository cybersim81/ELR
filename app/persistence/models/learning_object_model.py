from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.models.base import Base
from app.persistence.models.learning_object_value_models import (
    LearningObjectExampleModel,
    LearningObjectNoteModel,
)


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
        ForeignKey("categories.id"),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String,
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

    examples: Mapped[set[LearningObjectExampleModel]] = relationship(
        cascade="all, delete-orphan",
    )

    notes: Mapped[set[LearningObjectNoteModel]] = relationship(
        cascade="all, delete-orphan",
    )
