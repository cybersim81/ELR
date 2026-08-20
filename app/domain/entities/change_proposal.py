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
"""

change_type: ChangeType
change_payload: dict
proposal_rationale: str
change_evidence: tuple[dict, ...] = ()
change_metadata: dict = field(default_factory=dict)

id: UUID = field(default_factory=uuid4)
