from uuid import UUID

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.models.base import Base


class ChangeProposalModel(Base):
    """
    SQLAlchemy persistence model for ChangeProposal.
    """

    __tablename__ = "change_proposals"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )

    change_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    change_payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    proposal_rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    change_evidence: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    change_metadata: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
