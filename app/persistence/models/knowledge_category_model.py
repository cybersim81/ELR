from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base


class KnowledgeCategoryModel(Base):
    """SQLAlchemy persistence model for the KnowledgeCategory domain entity."""

    __tablename__ = "categories"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True,
    )
