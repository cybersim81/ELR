from enum import Enum


class ReviewDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_REVISION = "REQUEST_REVISION"
