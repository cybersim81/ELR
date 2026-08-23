from uuid import UUID

from app.application.errors import (
    EntityNotFound,
    InvalidOperation,
)
from app.domain.entities.audit_record import AuditRecord
from app.domain.entities.knowledge_statement import KnowledgeStatement
from app.domain.entities.learning_object import (
    InvalidStateTransition,
    LearningObject,
)
from app.domain.entities.version import Version
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.event_record_repository import (
    EventRecordRepository,
)
from app.domain.repositories.learning_object_repository import (
    LearningObjectRepository,
)
from app.domain.repositories.version_repository import VersionRepository
from app.events.event_record import EventRecord
from contextlib import nullcontext
from app.application.services.audit_service import AuditService
from app.application.services.version_service import VersionService



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
        event_record_repository: EventRecordRepository,
        transaction_factory=None,
        version_service: VersionService | None = None,
        audit_service: AuditService | None = None,
    ):
        self.learning_object_repository = learning_object_repository
        self.version_repository = version_repository
        self.audit_repository = audit_repository
        self.event_record_repository = event_record_repository
        self.transaction_factory = (
        transaction_factory or nullcontext
        )

        self.version_service = (
            version_service
            or VersionService(version_repository)
        )

        self.audit_service = (
            audit_service
            or AuditService(audit_repository)
        )


    def create_candidate(
        self,
        anchor_id: UUID,
        statement: KnowledgeStatement,
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

        try:
            learning_object.submit_for_review()
        except InvalidStateTransition as exc:
            raise InvalidOperation(
                "Learning object cannot be submitted for review."
            ) from exc

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

    def approve(
        self,
        learning_object_id: UUID,
        actor: str,
    ) -> LearningObject:
        """
        Proposed -> Active.

        Approval creates the first immutable Version and records
        the audit event within one transaction boundary.
        """
        with self.transaction_factory():
            learning_object = self._get_or_raise(learning_object_id)

            try:
                learning_object.approve()
            except InvalidStateTransition as exc:
                raise InvalidOperation(
                    "Learning object cannot be approved."
                ) from exc

            version = Version(
                learning_object_id=learning_object.id,
                number=1,
                snapshot={
                    "anchor_id": str(learning_object.anchor_id),
                    "statement": {
                        "text": learning_object.statement.text,
                        "language": learning_object.statement.language,
                    },
                    "category_id": str(learning_object.category_id),
                    "state": learning_object.state.value,
                },
            )

            self.learning_object_repository.save(
                learning_object
            )
            self.version_repository.save(version)

            self.audit_repository.record(
                AuditRecord(
                    entity_id=learning_object.id,
                    event_type="LearningObjectApproved",
                    actor=actor,
                    metadata={
                        "version": version.number,
                    },
                )
            )

            return learning_object


    def update_knowledge(
        self,
        learning_object_id: UUID,
        statement: KnowledgeStatement,
        actor: str,
    ) -> LearningObject:
        """
        Update the knowledge of an Active Learning Object.

        The LearningObject remains Active.
        A new immutable Version is created and the
        previous Version remains preserved in history.
        """

        learning_object = self._get_or_raise(
            learning_object_id
        )

        try:
            learning_object.update_knowledge(
                statement
            )
        except InvalidStateTransition as exc:
            raise InvalidOperation(
                "Learning object cannot be updated."
            ) from exc

        self.learning_object_repository.save(
            learning_object
        ) 

        version = self.version_service.create_version(
            learning_object
        )

        self.audit_service.record_event(
            entity_id=learning_object.id,
            event_type="LearningObjectUpdated",
            actor=actor,
            metadata={
                "version": version.number,
            },
        )

        self.event_record_repository.record(
            EventRecord(
                event_type="LearningObjectUpdated",
                event_source="LearningObjectService",
                aggregate_type="LearningObject",
                aggregate_id=learning_object.id,
                version=version.number,
                payload={
                    "learning_object_id": str(
                        learning_object.id
                    ),
                    "new_version": version.number,
                },
            )
        )

        return learning_object




    def retire(
        self,
        learning_object_id: UUID,
        actor: str,
    ) -> LearningObject:
        """
        Active -> Retired
        """

        learning_object = self._get_or_raise(
            learning_object_id
        )

        try:
            learning_object.retire()
        except InvalidStateTransition as exc:
            raise InvalidOperation(
                "Learning object cannot be retired."
            ) from exc

        self.learning_object_repository.save(
            learning_object
        )

        self.audit_repository.record(
            AuditRecord(
                entity_id=learning_object.id,
                event_type="LearningObjectRetired",
                actor=actor,
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
        Retrieve the immutable Version history
        of a Learning Object.
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
        Retrieve a Learning Object or raise a
        domain-level application exception.
        """

        learning_object = (
            self.learning_object_repository.get_by_id(
                learning_object_id
            )
        )

        if learning_object is None:
            raise EntityNotFound(
                f"Learning Object "
                f"{learning_object_id} not found"
            )

        return learning_object
