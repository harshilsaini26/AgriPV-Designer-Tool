"""Crop shade-response parameters and the hockey-stick yield curve (spec §12.3, §13)."""

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from apv_core.constants import SEASON_MONTHS, Season
from apv_core.ranges import Range

TOLERANCE_GROUPS = ("tolerant", "neutral", "sensitive")


class EvidenceGrade(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


@dataclass(frozen=True)
class CropParams:
    """Shade response for one crop.

    ``l_t`` (light threshold) and ``k`` (slope) hold one value per Case; the pessimistic
    case must never yield more than central, nor central more than optimistic.
    """

    id: str
    name: str
    seasons: frozenset[Season]
    tolerance: str
    l_t: Range
    k: Range
    grade: EvidenceGrade
    citations: tuple[str, ...] = ()
    user_entered: bool = False

    def __post_init__(self) -> None:
        if not self.seasons:
            raise ValueError(f"crop {self.id!r}: seasons must not be empty")
        if self.tolerance not in TOLERANCE_GROUPS:
            raise ValueError(f"crop {self.id!r}: tolerance must be one of {TOLERANCE_GROUPS}")
        lt = (self.l_t.pessimistic, self.l_t.central, self.l_t.optimistic)
        ks = (self.k.pessimistic, self.k.central, self.k.optimistic)
        if any(v is None or not 0.0 < v <= 1.0 for v in lt):
            raise ValueError(f"crop {self.id!r}: l_t values must be in (0, 1]")
        if any(v is None or v < 0.0 for v in ks):
            raise ValueError(f"crop {self.id!r}: k values must be >= 0")
        if not (lt[0] >= lt[1] >= lt[2]) or not (ks[0] >= ks[1] >= ks[2]):
            raise ValueError(
                f"crop {self.id!r}: need pessimistic >= central >= optimistic for both l_t and k"
            )


def relative_yield(light: float | np.ndarray, l_t: float, k: float) -> np.ndarray:
    """Yield relative to open field: 1 above the light threshold, then linear decline, clipped to [0, 1]."""
    light_arr = np.asarray(light, dtype=float)
    return np.clip(np.where(light_arr >= l_t, 1.0, 1.0 - k * (l_t - light_arr)), 0.0, 1.0)


def season_light(monthly_light: np.ndarray, season: Season) -> np.ndarray:
    """Mean light fraction over the season's months, along the last axis (month m at index m-1)."""
    idx = [m - 1 for m in SEASON_MONTHS[season]]
    return np.asarray(monthly_light, dtype=float)[..., idx].mean(axis=-1)


def is_selectable_by_default(crop: CropParams) -> bool:
    return crop.grade in (EvidenceGrade.A, EvidenceGrade.B, EvidenceGrade.C)


def needs_evidence_notice(crop: CropParams) -> bool:
    return crop.user_entered or crop.grade in (EvidenceGrade.C, EvidenceGrade.D)
