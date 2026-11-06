"""User-facing notices returned with every sweep (REQ-PRV-04). Named to avoid shadowing stdlib `warnings`."""

from dataclasses import dataclass
from enum import StrEnum


class NoticeCode(StrEnum):
    OUTSIDE_POLICY_LIMIT = "outside_policy_limit"
    NO_ALLOWED_GCR = "no_allowed_gcr"
    LOW_EVIDENCE_CROP = "low_evidence_crop"
    USER_ENTERED_VALUES = "user_entered_values"
    KUSUM_SIZE_OUT_OF_RANGE = "kusum_size_out_of_range"
    IRR_UNDEFINED = "irr_undefined"
    LEASE_NOT_VIABLE = "lease_not_viable"


@dataclass(frozen=True)
class Notice:
    code: NoticeCode
    message: str
    gcr: float | None = None
