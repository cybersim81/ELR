from app.domain.entities.audit_record import AuditRecord
from app.domain.entities.learning_object import LearningObject
from app.domain.entities.version import Version


class InMemoryLearningObjectRepository:
    """
    In-memory implementation of the LearningObjectRepository
    contract for tests.
    """

    def __init__(self):
        self.items: dict = {}

    def save(
        self,
        learning_object: LearningObject,
    ) -> None:
        self.items[learning_object.id] = learning_object

    def get_by_id(
        self,
        object_id,
    ) -> LearningObject | None:
        return self.items.get(object_id)


class InMemoryVersionRepository:
    """
    In-memory implementation of the VersionRepository
    contract for tests.
    """

    def __init__(self):
        self.items: list[Version] = []

    def save(
        self,
        version: Version,
    ) -> None:
        self.items.append(version)

    def get_history(
        self,
        learning_object_id,
    ) -> list[Version]:
        return [
            version
            for version in self.items
            if version.learning_object_id == learning_object_id
        ]


class InMemoryAuditRepository:
    """
    In-memory implementation of the AuditRepository
    contract for tests.
    """

    def __init__(self):
        self.items: list[AuditRecord] = []

    def record(
        self,
        audit: AuditRecord,
    ) -> None:
        self.items.append(audit)

    def find_by_entity(
        self,
        entity_id,
    ) -> list[AuditRecord]:
        return [
            audit
            for audit in self.items
            if audit.entity_id == entity_id
        ]
