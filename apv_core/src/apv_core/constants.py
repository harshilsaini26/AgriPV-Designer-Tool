"""Fixed grids, units and defaults shared across apv_core (spec §12, PRD Global Constraints)."""

from enum import StrEnum


class Season(StrEnum):
    KHARIF = "kharif"
    RABI = "rabi"
    ZAID = "zaid"


# Month numbers, 1 = January.
SEASON_MONTHS: dict[Season, tuple[int, ...]] = {
    Season.KHARIF: (6, 7, 8, 9, 10),
    Season.RABI: (11, 12, 1, 2, 3),
    Season.ZAID: (3, 4, 5, 6),
}

GCR_GRID: tuple[float, ...] = tuple(round(0.05 * i, 2) for i in range(11))

ACRE_M2 = 4046.86
ANALYSIS_YEARS = 25

DEFAULT_POLICY_LIMIT = 0.80
POLICY_LIMIT_MIN = 0.50
POLICY_LIMIT_MAX = 1.00

KUSUM_A_MIN_MW = 0.5
KUSUM_A_MAX_MW = 2.0

DEFAULT_RANGE_SPREAD = 0.10
DEFAULT_APV_COST_PREMIUM = 0.05

TOL = 1e-9
