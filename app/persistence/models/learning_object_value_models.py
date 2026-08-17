from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class LearningObjectExampleModel(Base):
    __tablename__ = "learning_object_examples"

    learning_object_id: Mapped[UUID] = mapped_column(
        ForeignKey("learning_objects.id"),
        primary_key=True,
    )

    content: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )


class LearningObjectNoteModel(Base):
    __tablename__ = "learning_object_notes"

    learning_object_id: Mapped[UUID] = mapped_column(
        ForeignKey("learning_objects.id"),
        primary_key=True,
    )

    content: Mapped[str] = mapped_column(
        String,
        primary_key=True,
    )
