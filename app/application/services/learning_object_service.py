from __future__ import annotations

from uuid import UUID

from app.application.services.audit_service import AuditService
from app.application.services.authorization_service import AuthorizationService
from app.application.services.version_service import VersionService
from app.domain.entities.audit_record import AuditRecord
from app.domain.entities.learning_object import LearningObject
from app.domain.entities.version import Version
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.learning_object_repository import LearningObjectRepository
from app.domain.repositories.version_repository import VersionRepository
from app.domain.value_objects.knowledge_statement import KnowledgeStatement
from app.domain.value_objects.lifecycle_state import LifecycleState
from app.events.event_record import EventRecord
from app.events.event_record_repository import EventRecordRepository


class LearningObjectService:
    """Application service coordinating LearningObject lifecycle operations."""

    def __init__(
        self,
        repository: LearningObjectRepository,
        version_repository: VersionRepository,
        audit_repository: AuditRepository,
        authorization_service: AuthorizationService | None = None,
        version_service: VersionService | None = None,
        audit_service: AuditService | None = None,
        event_record_repository: EventRecordRepository | None = None,
    ) -> None:
        self.repository = repository
        self.version_repository = version_repository
        self.audit_repository = audit_repository
        self.authorization_service = (
            authorization_service or AuthorizationService()
        )
        self.version_service = (
            version_service or VersionService(version_repository)
        )
        self.audit_service = (
            audit_service or AuditService(audit_repository)
        )
        self.event_record_repository = event_record_repository

    def create_candidate(
        self,
        *,
        statement: KnowledgeStatement,
        anchor_id: UUID,
        knowledge_category_id: UUID,
        actor_id: UUID | None = None,
    ) -> LearningObject:
        self.authorization_service.require("create_learning_object")

        learning_object = LearningObject(
            statement=statement,
            anchor_id=anchor_id,
            knowledge_category_id=knowledge_category_id,
        )

        self.repository.add(learning_object)

        self.audit_service.record_event(
            entity_id=learning_object.id,
            actor_id=actor_id,
            event_type="created",
            metadata={},
        )

        return learning_object

    def submit_for_review(
        self,
        learning_object_id: UUID,
        *,
        actor_id: UUID | None = None,
    ) -> LearningObject:
        self.authorization_service.require("submit_learning_object")

        learning_object = self.repository.get(learning_object_id)
        learning_object.submit_for_review()

        self.repository.update(learning_object)

        self.audit_service.record_event(
            entity_id=learning_object.id,
            actor_id=actor_id,
            event_type="submitted_for_review",
            metadata={},
        )

        return learning_object

    def approve(
        self,
        learning_object_id: UUID,
        *,
        actor_id: UUID | None = None,
    ) -> LearningObject:
        self.authorization_service.require("approve_learning_object")

        learning_object = self.repository.get(learning_object_id)
        learning_object.approve()

        self.repository.update(learning_object)

        self.audit_service.record_event(
            entity_id=learning_object.id,
            actor_id=actor_id,
            event_type="approved",
            metadata={},
        )

        return learning_object

    def update_knowledge(
        self,
        learning_object_id: UUID,
        *,
        statement: KnowledgeStatement,
        actor_id: UUID | None = None,
    ) -> Version:
        self.authorization_service.require("update_learning_object")

        learning_object = self.repository.get(learning_object_id)

        learning_object.update_knowledge(statement)

        version = self.version_service.create_version(
            learning_object=learning_object,
        )

        self.repository.update(learning_object)

        self.audit_service.record_event(
            entity_id=learning_object.id,
            actor_id=actor_id,
            event_type="updated",
            metadata={
                "version_id": str(version.id),
                "version_number": version.version_number,
            },
        )

        return version

    def retire(
        self,
        learning_object_id: UUID,
        *,
        actor_id: UUID | None = None,
    ) -> LearningObject:
        self.authorization_service.require("retire_learning_object")

        learning_object = self.repository.get(learning_object_id)
        learning_object.retire()

        self.repository.update(learning_object)

        self.audit_service.record_event(
            entity_id=learning_object.id,
            actor_id=actor_id,
            event_type="retired",
            metadata={},
        )

        return learning_object

    def get(self, learning_object_id: UUID) -> LearningObject:
        self.authorization_service.require("read_learning_object")

        return self.repository.get(learning_object_id)

    def get_version_history(
        self,
        learning_object_id: UUID,
    ) -> list[Version]:
        self.authorization_service.require("read_learning_object")

        return self.version_service.get_versions(
            learning_object_id,
        )

    def get_audit_history(
        self,
        learning_object_id: UUID,
    ) -> list[AuditRecord]:
        self.authorization_service.require("read_audit_history")

        return self.audit_service.get_events(
            learning_object_id,
        )

    def get_event_history(
        self,
        learning_object_id: UUID,
    ) -> list[EventRecord]:
        self.authorization_service.require("read_event_history")

        if self.event_record_repository is None:
            return []

        return self.event_record_repository.find_by_entity(
            learning_object_id,
        )
