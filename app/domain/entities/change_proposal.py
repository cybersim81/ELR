from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class ChangeType(str, Enum):
    CREATE = "CREATE"
    MERGE = "MERGE"
    UPDATE = "UPDATE"


@dataclass(frozen=True)
class ChangeProposal:
    """
    Atomic proposal for a change to the ELR.

    The proposal describes what the KEP proposes to change.
    It does not approve, reject, or persist the change.

    Review semantics belong to the Learning Review process.

    A revised proposal preserves explicit provenance to the
    previous proposal and the Review Decision Trace that
    requested the revision.
    """

    change_type: ChangeType
    change_payload: dict
    proposal_rationale: str
    change_evidence: tuple[dict, ...] = ()
    change_metadata: dict = field(default_factory=dict)

    id: UUID = field(default_factory=uuid4)

    previous_proposal_id: UUID | None = None
    previous_review_trace_id: UUID | None = None
    revision_number: int = 1

    def __post_init__(self) -> None:
        if not self.change_payload:
            raise ValueError(
                "Change Proposal payload cannot be empty."
            )

        if not self.proposal_rationale.strip():
            raise ValueError(
                "Change Proposal rationale cannot be empty."
            )

        if not self.change_evidence:
            raise ValueError(
                "Change Evidence is required."
            )

        if self.revision_number < 1:
            raise ValueError(
                "Revision number must be greater than zero."
            )

        has_previous_proposal = (
            self.previous_proposal_id is not None
        )
        has_previous_trace = (
            self.previous_review_trace_id is not None
        )

        if self.revision_number == 1:
            if has_previous_proposal or has_previous_trace:
                raise ValueError(
                    "Initial Change Proposal cannot reference a previous revision."
                )
        else:
            if not has_previous_proposal:
                raise ValueError(
                    "Revised Change Proposal must reference "
                    "the previous proposal."
                )

            if not has_previous_trace:
                raise ValueError(
                    "Revised Change Proposal must reference "
                    "the previous Review Decision Trace."
                )
