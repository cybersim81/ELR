```python
from uuid import UUID

from app.domain.entities.audit_record import AuditRecord
from app.domain.entities.learning_object import LearningObject
from app.domain.entities.version import Version
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.learning_object_repository import (
    LearningObjectRepository,
)
from app.domain.repositories.version_repository import VersionRepository


class LearningObjectNotFound(Exception):
    pass


class LearningObjectService:
    """
    Application service for Learning Object use cases.

    This service coordinates domain operations and repositories.
    It contains no database or HTTP-specific logic.
    """

    def __init__(
        self,
        learning_object_repository: LearningObjectRepository,
        version_repository: VersionRepository,
        audit_repository: AuditRepository,
    ):
        self.learning_object_repository = learning_object_repository
        self.version_repository = version_repository
        self.audit_repository = audit_repository

    def create_candidate(
        self,
        anchor_id: UUID,
        statement: str,
        category_id: UUID,
        actor: str,
    ) -> LearningObject:
        """
        Create a new Learning Object in Candidate state.
        """

        learning_object = LearningObject(
            anchor_id=anchor_id,
            statement=statement,
            category_id=category_id,
        )

        self.learning_object_repository.save(
            learning_object
        )

        self.audit_repository.record(
            AuditRecord(
                entity_id=learning_object.id,
                event_type="LearningObjectCreated",
                actor=actor,
            )
        )

        return learning_object

    def submit_for_review(
        self,
        learning_object_id: UUID,
        actor: str,
    ) -> LearningObject:
        """
        Candidate -> Proposed
        """

        learning_object = self._get_or_raise(
            learning_object_id
        )

        learning_object.submit_for_review()

        self.learning_object_repository.save(
            learning_object
        )

        self.audit_repository.record(
            AuditRecord(
                entity_id=learning_object.id,
                event_type="LearningObjectSubmitted",
                actor=actor,
            )
        )

        return learning_object

    def mark_reviewed(
        self,
        learning_object_id: UUID,
        actor: str,
    ) -> LearningObject:
        """
        Proposed -> Reviewed
        """

        learning_object = self._get_or_raise(
            learning_object_id
        )

        learning_object.mark_reviewed()

        self.learning_object_repository.save(
            learning_object
        )

        self.audit_repository.record(
            AuditRecord(
                entity_id=learning_object.id,
                event_type="LearningObjectReviewed",
                actor=actor,
            )
        )

        return learning_object

    def approve(
        self,
        learning_object_id: UUID,
        actor: str,
    ) -> LearningObject:
        """
        Reviewed -> Active

        Approval also creates the first immutable version
        and records an audit event.
        """

        learning_object = self._get_or_raise(
            learning_object_id
        )

        learning_object.approve()

        version = Version(
            entity_id=learning_object.id,
            number=learning_object.version,
            snapshot={
                "anchor_id": str(
                    learning_object.anchor_id
                ),
                "statement": learning_object.statement,
                "category_id": str(
                    learning_object.category_id
                ),
                "state": learning_object.state.value,
            },
        )

        self.learning_object_repository.save(
            learning_object
        )

        self.version_repository.save(
            version
        )

        self.audit_repository.record(
            AuditRecord(
                entity_id=learning_object.id,
                event_type="LearningObjectApproved",
                actor=actor,
                metadata={
                    "version": learning_object.version,
                },
            )
        )

        return learning_object

    def get(
        self,
        learning_object_id: UUID,
    ) -> LearningObject:
        """
        Retrieve a Learning Object.
        """

        return self._get_or_raise(
            learning_object_id
        )

    def get_history(
        self,
        learning_object_id: UUID,
    ) -> list[Version]:
        """
        Retrieve the immutable version history.
        """

        self._get_or_raise(
            learning_object_id
        )

        return self.version_repository.get_history(
            learning_object_id
        )

    def _get_or_raise(
        self,
        learning_object_id: UUID,
    ) -> LearningObject:
        """
        Retrieve a Learning Object or raise a domain-level
        application exception when it does not exist.
        """

        learning_object = (
            self.learning_object_repository.get_by_id(
                learning_object_id
            )
        )

        if learning_object is None:
            raise LearningObjectNotFound(
                f"Learning Object "
                f"{learning_object_id} not found"
            )

        return learning_object
```
