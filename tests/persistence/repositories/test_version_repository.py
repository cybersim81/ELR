from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.entities.version import Version
from app.domain.repositories.version_repository import VersionRepository
from app.persistence.repositories.version_repository import (
    SQLAlchemyVersionRepository,
)


def test_version_repository_implements_domain_contract() -> None:
    repository = SQLAlchemyVersionRepository(Session())

    assert isinstance(repository, VersionRepository)


def test_version_repository_save_adds_version_model() -> None:
    session = Session()
    repository = SQLAlchemyVersionRepository(session)

    version = Version(
        learning_object_id=uuid4(),
        number=1,
        snapshot={"statement": "Test snapshot"},
    )

    repository.save(version)

    model = session.new.pop()

    assert model.id == version.id
    assert model.learning_object_id == version.learning_object_id
    assert model.number == version.number
    assert model.snapshot == version.snapshot
    assert model.created_at == version.created_at
