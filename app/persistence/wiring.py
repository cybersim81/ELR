from sqlalchemy.orm import Session

from app.application.services.learning_object_service import LearningObjectService
from app.persistence.database import SessionFactory
from app.persistence.repositories.audit_repository import (
    SQLAlchemyAuditRepository,
)
from app.persistence.repositories.learning_object_repository import (
    SQLAlchemyLearningObjectRepository,
)
from app.persistence.repositories.version_repository import (
    SQLAlchemyVersionRepository,
)
from app.persistence.transaction import transaction


def create_learning_object_service(
    session: Session | None = None,
) -> tuple[LearningObjectService, Session]:
    session = session or SessionFactory()

    service = LearningObjectService(
        learning_object_repository=SQLAlchemyLearningObjectRepository(
            session
        ),
        version_repository=SQLAlchemyVersionRepository(
            session
        ),
        audit_repository=SQLAlchemyAuditRepository(
            session
        ),
        transaction_factory=lambda: transaction(session),
    )

    return service, session
