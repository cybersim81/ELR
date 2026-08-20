from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base


class ReviewDecisionTraceModel(Base):
    """
    SQLAlchemy persistence model for ReviewDecisionTrace.
    """

    __tablename__ = "review_decision_traces"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )

    proposal_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    decision: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    reviewer: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
