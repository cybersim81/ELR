from uuid import UUID

from app.domain.entities.learning_object import LearningObject
from app.domain.entities.version import Version
from app.domain.repositories.version_repository import VersionRepository

class VersionService:
    """Application boundary for Learning Object version coordination."""


    def __init__(
        self,
        version_repository: VersionRepository,
    ) -> None:
        self._version_repository = version_repository

    def create_version(
        self,
        learning_object: LearningObject,
    ) -> Version:
        """Create and persist the next immutable snapshot."""
        history = self._version_repository.get_history(
            learning_object.id
        )

        next_version_number = (
            max(
                (
                    version.number
                    for version in history
                ),
                default=0,
            )
            \+ 1
        )

        version = Version(
            learning_object_id=learning_object.id,
            number=next_version_number,
            snapshot={
                "anchor_id": str(
                    learning_object.anchor_id
                ),
                "statement": {
                    "text": (
                        learning_object.statement.text
                    ),
                    "language": (
                        learning_object.statement.language
                    ),
                },
                "category_id": str(
                    learning_object.category_id
                ),
                "state": (
                    learning_object.state.value
                ),
            },
        )

        self._version_repository.save(version)

        return version

    def get_versions(
        self,
        learning_object_id: UUID,
    ) -> list[Version]:
        """Return the immutable version history."""
        return self._version_repository.get_history(
            learning_object_id
        )
