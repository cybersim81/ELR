from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from .example import Example
from .note import Note


class LearningObjectState(str, Enum):
    CANDIDATE = "Candidate"
    PROPOSED = "Proposed"
    REVIEWED = "Reviewed"
    ACTIVE = "Active"
    UPDATED = "Updated"
    RETIRED = "Retired"
    REJECTED = "Rejected"


class InvalidStateTransition(Exception):
    pass


@dataclass
class LearningObject:
    """
    Core domain entity representing an ELR Learning Object.

    This entity contains domain rules only.
    It has no dependency on:
    - database
    - API
    - framework
    - external services
    """

    anchor_id: UUID
    statement: str
    category_id: UUID

    examples: set[Example] = field(default_factory=set)
    notes: set[Note] = field(default_factory=set)

    id: UUID = field(default_factory=uuid4)
    state: LearningObjectState = LearningObjectState.CANDIDATE

    version: int = 1

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def submit_for_review(self) -> None:
        """
        Candidate -> Proposed
        """

        self._transition(
            LearningObjectState.PROPOSED,
            allowed=[
                LearningObjectState.CANDIDATE
            ]
        )

    def mark_reviewed(self) -> None:
        """
        Proposed -> Reviewed
        """

        self._transition(
            LearningObjectState.REVIEWED,
            allowed=[
                LearningObjectState.PROPOSED
            ]
        )

    def approve(self) -> None:
        """
        Reviewed -> Active
        """

        self._transition(
            LearningObjectState.ACTIVE,
            allowed=[
                LearningObjectState.REVIEWED
            ]
        )

    def reject(self) -> None:
        """
        Proposed/Reviewed -> Rejected
        """

        self._transition(
            LearningObjectState.REJECTED,
            allowed=[
                LearningObjectState.PROPOSED,
                LearningObjectState.REVIEWED
            ]
        )

    def update_version(self) -> None:
        """
        Creates a new version.

        Previous history must be preserved
        by persistence layer.
        """

        if self.state not in [
            LearningObjectState.ACTIVE,
            LearningObjectState.UPDATED
        ]:
            raise InvalidStateTransition(
                "Only active objects can be updated"
            )

        self.version += 1
        self.state = LearningObjectState.UPDATED
        self.updated_at = datetime.now(timezone.utc)

    def retire(self) -> None:
        """
        Active/Updated -> Retired
        """

        self._transition(
            LearningObjectState.RETIRED,
            allowed=[
                LearningObjectState.ACTIVE,
                LearningObjectState.UPDATED
            ]
        )

    def _transition(
        self,
        target: LearningObjectState,
        allowed: list[LearningObjectState]
    ) -> None:

        if self.state not in allowed:
            raise InvalidStateTransition(
                f"Cannot transition from "
                f"{self.state.value} to {target.value}"
            )

        self.state = target
        self.updated_at = datetime.now(timezone.utc)
