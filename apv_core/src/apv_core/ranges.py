"""Scenario cases and the three-value Range used for every headline result."""

from dataclasses import dataclass
from enum import StrEnum


class Case(StrEnum):
    """Scenario case. Values in a Range are case outputs, not sorted min/max."""

    PESSIMISTIC = "pessimistic"
    CENTRAL = "central"
    OPTIMISTIC = "optimistic"


@dataclass(frozen=True)
class Range:
    pessimistic: float | None
    central: float | None
    optimistic: float | None

    def get(self, case: Case) -> float | None:
        return getattr(self, Case(case).value)
