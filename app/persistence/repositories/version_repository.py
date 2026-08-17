from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.entities.version import Version
from app.domain.repositories.version_repository import VersionRepository
from app.persistence.models.version_model import VersionModel


class SQLAlchemyVersionRepository(VersionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, version: Version) -> None:
        model = VersionModel(
            id=version.id,
            learning_object_id=version.learning_object_id,
            number=version.number,
            snapshot=version.snapshot,
            created_at=version.created_at,
        )

        self._session.add(model)

    def get_history(self, learning_object_id: UUID) -> list[Version]:
        models = (
            self._session.query(VersionModel)
            .filter(
                VersionModel.learning_object_id == learning_object_id
            )
            .order_by(VersionModel.number.asc())
            .all()
        )

        return [
            Version(
                id=model.id,
                learning_object_id=model.learning_object_id,
                number=model.number,
                snapshot=model.snapshot,
                created_at=model.created_at,
            )
            for model in models
        ]
