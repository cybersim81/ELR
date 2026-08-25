```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from .example import Example
from .knowledge_statement import KnowledgeStatement
from .note import Note


class LearningObjectState(str, Enum):
    ACTIVE = "Active"
    RETIRED = "Retired"


class InvalidStateTransition(Exception):
    pass


@dataclass
class LearningObject:
    """
    Aggregate root representing persistent ELR knowledge.

    A LearningObject represents knowledge that has already passed
    the proposal/review boundary and entered the ELR.

    Change Proposal creation and Learning Review are therefore not
    part of this aggregate's lifecycle.

    KnowledgeStatement is owned by this aggregate.
    """

    anchor_id: UUID
    statement: KnowledgeStatement
    category_id: UUID

    examples: set[Example] = field(default_factory=set)
    notes: set[Note] = field(default_factory=set)

    id: UUID = field(default_factory=uuid4)

    state: LearningObjectState = LearningObjectState.ACTIVE

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
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

        Knowledge updates are performed against an existing active
        LearningObject. Version creation/history preservation is
        handled by the application versioning boundary.

        Lifecycle state remains Active.
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
```
