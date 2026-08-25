from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from .example import Example
from .knowledge_statement import KnowledgeStatement
from .note import Note


class LearningObjectState(str, Enum):
    CANDIDATE = "Candidate"
    PROPOSED = "Proposed"
    ACTIVE = "Active"
    RETIRED = "Retired"


class InvalidStateTransition(Exception):
    pass


@dataclass
class LearningObject:
    """
    Aggregate root representing persistent ELR knowledge.

    The Learning Object has an explicit lifecycle:

        Candidate -> Proposed -> Active -> Retired

    Review decisions such as APPROVE, REJECT and REQUEST_REVISION
    belong to the Change Proposal / Learning Review process and are
    not Learning Object states.

    KnowledgeStatement is owned by this aggregate.
    """

    anchor_id: UUID
    statement: KnowledgeStatement
    category_id: UUID

    examples: set[Example] = field(default_factory=set)
    notes: set[Note] = field(default_factory=set)

    id: UUID = field(default_factory=uuid4)

    state: LearningObjectState = LearningObjectState.CANDIDATE

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def submit_for_review(self) -> None:
        """
        Candidate -> Proposed.

        The Learning Object enters the proposed lifecycle state.
        The actual review decision remains owned by Learning Review.
        """

        self._transition(
            LearningObjectState.PROPOSED,
            allowed=[
                LearningObjectState.CANDIDATE,
            ],
        )

    def approve(self) -> None:
        """
        Proposed -> Active.

        This method performs only the domain lifecycle transition.

        It does not decide whether a Change Proposal is approved.
        That decision belongs to the Learning Review process.
        """

        self._transition(
            LearningObjectState.ACTIVE,
            allowed=[
                LearningObjectState.PROPOSED,
            ],
        )

    def retire(self) -> None:
        """
        Active -> Retired.
        """

        self._transition(
            LearningObjectState.RETIRED,
            allowed=[
                LearningObjectState.ACTIVE,
            ],
        )

    def update_knowledge(
        self,
        statement: KnowledgeStatement,
    ) -> None:
        """
        Replace the aggregate's current knowledge value.

        The Learning Object must already be Active.

        Lifecycle state remains Active.
        Version creation and history preservation are handled by
        the application/versioning boundary.
        """

        if self.state != LearningObjectState.ACTIVE:
            raise InvalidStateTransition(
                "Only active Learning Objects can be updated"
            )

        self.statement = statement
        self.updated_at = datetime.now(timezone.utc)

    def _transition(
        self,
        target: LearningObjectState,
        allowed: list[LearningObjectState],
    ) -> None:

        if self.state not in allowed:
            raise InvalidStateTransition(
                f"Cannot transition from "
                f"{self.state.value} to {target.value}"
            )

        self.state = target
        self.updated_at = datetime.now(timezone.utc)
