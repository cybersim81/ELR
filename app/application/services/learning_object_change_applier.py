from uuid import UUID

from app.application.errors import InvalidOperation
from app.application.services.audit_service import AuditService
from app.application.services.version_service import VersionService
from app.application.services.change_applier import ChangeApplier
from app.domain.entities.audit_record import AuditRecord
from app.domain.entities.change_proposal import ChangeProposal, ChangeType
from app.domain.entities.knowledge_statement import KnowledgeStatement
from app.domain.entities.learning_object import LearningObject
from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.learning_object_repository import (
    LearningObjectRepository,
)
from app.domain.repositories.version_repository import VersionRepository


class LearningObjectChangeApplier(ChangeApplier):
    """
    Apply approved Change Proposals to the Learning Object repository.

    This class is deliberately downstream of Learning Review.

    It does not:
    - perform review;
    - validate knowledge;
    - decide whether a proposal is acceptable;
    - create Change Proposals.

    It only applies proposals that already have an APPROVE decision.
    """

    def __init__(
        self,
        learning_object_repository: LearningObjectRepository,
        version_service: VersionService,
        audit_service: AuditService,
    ) -> None:
        self.learning_object_repository = (
            learning_object_repository
        )
        self.version_service = version_service
        self.audit_service = audit_service

    def apply(
        self,
        proposal: ChangeProposal,
        review_trace: ReviewDecisionTrace,
        actor: str,
    ) -> LearningObject:
        """
        Apply an approved Change Proposal.

        CREATE is the only supported change type at this stage.
        """

        self._ensure_approved(
            proposal,
            review_trace,
        )

        if proposal.change_type is not ChangeType.CREATE:
            raise InvalidOperation(
                "Only CREATE Change Proposals are supported "
                "by this applier."
            )

        learning_object = self._create_learning_object(
            proposal
        )

        self.learning_object_repository.save(
            learning_object
        )

        version = self.version_service.create_version(
            learning_object
        )

        self.audit_service.record_event(
            entity_id=learning_object.id,
            event_type="LearningObjectCreated",
            actor=actor,
            metadata={
                "version": version.number,
                "proposal_id": str(proposal.id),
                "review_trace_id": str(review_trace.id),
            },
        )

        return learning_object

    @staticmethod
    def _ensure_approved(
        proposal: ChangeProposal,
        review_trace: ReviewDecisionTrace,
    ) -> None:
        if review_trace.proposal_id != proposal.id:
            raise InvalidOperation(
                "Review Decision Trace does not belong "
                "to the Change Proposal."
            )

        if review_trace.decision is not ReviewDecision.APPROVE:
            raise InvalidOperation(
                "Only approved Change Proposals can be applied."
            )

    @staticmethod
    def _create_learning_object(
        proposal: ChangeProposal,
    ) -> LearningObject:
        payload = proposal.change_payload

        try:
            anchor_id = UUID(
                str(payload["anchor_id"])
            )
            category_id = UUID(
                str(payload["category_id"])
            )

            statement_payload = payload["statement"]

            statement = KnowledgeStatement(
                text=statement_payload["text"],
                language=statement_payload["language"],
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise InvalidOperation(
                "CREATE Change Proposal contains an invalid "
                "Learning Object payload."
            ) from exc

        return LearningObject(
            anchor_id=anchor_id,
            statement=statement,
            category_id=category_id,
        )
