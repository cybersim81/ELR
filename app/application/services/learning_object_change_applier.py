from uuid import UUID

from app.application.errors import InvalidOperation
from app.application.services.audit_service import AuditService
from app.application.services.change_applier import ChangeApplier
from app.application.services.version_service import VersionService
from app.domain.entities.change_proposal import (
    ChangeProposal,
    ChangeType,
)
from app.domain.entities.knowledge_statement import KnowledgeStatement
from app.domain.entities.learning_object import (
    InvalidStateTransition,
    LearningObject,
)
from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.domain.repositories.learning_object_repository import (
    LearningObjectRepository,
)


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

        CREATE creates a new Learning Object.
        MERGE and UPDATE evolve an existing Learning Object
        while preserving its identity.
        """

        self._ensure_approved(
            proposal,
            review_trace,
        )

        if proposal.change_type is ChangeType.CREATE:
            return self._apply_create(
                proposal,
                review_trace,
                actor,
            )

        if proposal.change_type is ChangeType.MERGE:
            return self._apply_merge(
                proposal,
                review_trace,
                actor,
            )

        if proposal.change_type is ChangeType.UPDATE:
            return self._apply_update(
                proposal,
                review_trace,
                actor,
            )

        raise InvalidOperation(
            "Unsupported Change Proposal type."
        )

    def _apply_create(
        self,
        proposal: ChangeProposal,
        review_trace: ReviewDecisionTrace,
        actor: str,
    ) -> LearningObject:
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

    def _apply_merge(
        self,
        proposal: ChangeProposal,
        review_trace: ReviewDecisionTrace,
        actor: str,
    ) -> LearningObject:
        learning_object = self._get_target_learning_object(
            proposal
        )

        statement = self._statement_from_payload(
            proposal
        )

        try:
            learning_object.update_knowledge(
                statement
            )
        except InvalidStateTransition as exc:
            raise InvalidOperation(
                "Learning object cannot be merged."
            ) from exc

        self.learning_object_repository.save(
            learning_object
        )

        version = self.version_service.create_version(
            learning_object
        )

        self.audit_service.record_event(
            entity_id=learning_object.id,
            event_type="LearningObjectMerged",
            actor=actor,
            metadata={
                "version": version.number,
                "proposal_id": str(proposal.id),
                "review_trace_id": str(review_trace.id),
            },
        )

        return learning_object

    def _apply_update(
        self,
        proposal: ChangeProposal,
        review_trace: ReviewDecisionTrace,
        actor: str,
    ) -> LearningObject:
        learning_object = self._get_target_learning_object(
            proposal
        )

        statement = self._statement_from_payload(
            proposal
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
                "proposal_id": str(proposal.id),
                "review_trace_id": str(review_trace.id),
            },
        )

        return learning_object

    def _get_target_learning_object(
        self,
        proposal: ChangeProposal,
    ) -> LearningObject:
        try:
            learning_object_id = UUID(
                str(
                    proposal.change_payload[
                        "learning_object_id"
                    ]
                )
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise InvalidOperation(
                "Change Proposal target Learning Object "
                "id is invalid."
            ) from exc

        learning_object = (
            self.learning_object_repository.get_by_id(
                learning_object_id
            )
        )

        if learning_object is None:
            raise InvalidOperation(
                "Change Proposal target Learning Object "
                "was not found."
            )

        if learning_object.id != learning_object_id:
            raise InvalidOperation(
                "Change Proposal target Learning Object "
                "identity mismatch."
            )

        return learning_object

    @staticmethod
    def _statement_from_payload(
        proposal: ChangeProposal,
    ) -> KnowledgeStatement:
        try:
            statement_payload = (
                proposal.change_payload["statement"]
            )

            return KnowledgeStatement(
                text=statement_payload["text"],
                language=statement_payload["language"],
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise InvalidOperation(
                "Change Proposal contains an invalid "
                "Knowledge Statement."
            ) from exc

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
